from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from django.db.models import Q

from app.models import Module, Sem, Year, Question, Option, Profile, UserAnswer, DailyQuestion
from django.utils import timezone
from datetime import timedelta
from datetime import datetime, time

def generate_daily_questions(user):
    existing_questions = DailyQuestion.objects.filter(user=user, status=False).values_list('question', flat=True)

    if user.profile.sem == Sem.TWO:
        questions = Question.objects.filter(
            Q(module__sem=user.profile.sem) | Q(module__year_long=True),
            Q(module__year=user.profile.year),
        )
    else:
        questions = Question.objects.filter(
            Q(module__sem=user.profile.sem) | Q(module__year_long=True),
            Q(module__year=user.profile.year),
            sem=Sem.ONE
        )

    selected_questions = questions.exclude(qid__in=existing_questions).order_by('?')[:5]

    # delete old questions
    DailyQuestion.objects.filter(user=user).delete()

    for question in selected_questions:
        DailyQuestion.objects.create(
            user=user,
            question=question,
            status=False
        )

@login_required
def home(request):
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        answer = request.POST.get('text_answer')
        question_set = get_object_or_404(DailyQuestion, question__qid=question_id, user=request.user)
        # set status to True
        question_set.status = True
        question_set.save()
        # save answer
        if not question_set.question.is_mcq:
            UserAnswer.objects.create(
                user=request.user,
                question=question_set.question,
                answer=answer,
            )
        # update profile streak
        request.user.profile.add_streak()
        return redirect('home')

    today = timezone.now().date()
    daily_question = DailyQuestion.objects.filter(
        user=request.user,
        date=today
    ).first()

    is_redirect_attempt = request.session.get('daily_questions_redirect_attempted', False)


    if not daily_question or daily_question.date != today:
        if not is_redirect_attempt:
            generate_daily_questions(request.user)
            request.session['daily_questions_redirect_attempted'] = True
            return redirect('home')
        else:
            del request.session['daily_questions_redirect_attempted']

    pending_questions = DailyQuestion.objects.filter(
        user=request.user,
        status=False,
    ).select_related('question').prefetch_related('question__option_set')

    completed_questions = DailyQuestion.objects.filter(
        user=request.user,
        status=True,
    )

    context = {
        'pending_questions': pending_questions,
        'completed_questions': completed_questions,
    }

    return render(request, 'home.html', context)


@login_required
def view_modules(request):
    modules = Module.objects.all()
    return render(request, 'modules.html', {'modules': modules,'years': Year.choices})

@login_required
def list_question(request):
    code = request.GET.get('module')
    module = get_object_or_404(Module, code=code)
    if request.user.profile.sem == Sem.TWO:
        questions = Question.objects.filter(module__code=code).order_by('date_added')
    else:
        questions = Question.objects.filter(module__code=code, sem=Sem.ONE).order_by('date_added')
    questions=questions.order_by('date_added').prefetch_related('option_set')
    return render(request, 'qbank.html', {'module': module,'questions':questions})

@login_required
def flash_cards(request):
    modules = Module.objects.filter(Q(sem=request.user.profile.sem) | Q(year_long=True), year=request.user.profile.year)

    questions= None
    selected_module = request.GET.get('module')
    need_mcq = request.GET.get('need_mcq')
    if selected_module:
        if selected_module == 'all':
            if request.user.profile.sem == Sem.TWO:
                questions = Question.objects.filter(module__in=modules)
            else:
                questions = Question.objects.filter(module__in=modules, sem=Sem.ONE)
        else:
            selected_module = get_object_or_404(Module, code=selected_module)
            print(selected_module)
            if request.user.profile.sem == Sem.TWO:
                questions = Question.objects.filter(module=selected_module)
            else:
                questions = Question.objects.filter(module=selected_module, sem=Sem.ONE)
        print(questions)
        if need_mcq:
            questions = questions.filter(is_mcq=True)
        else:
            questions = questions.filter(is_mcq=False)
    print(questions)
    return render(request, 'flash_cards.html', {'modules': modules,'questions':questions, 'selected_module': selected_module, 'need_mcq': need_mcq})

@login_required
def add_question(request, qid=None):

    selected_module=None
    all_modules = Module.objects.all()
    if 'module' in request.GET:
        selected_module = get_object_or_404(Module, code=request.GET['module'])

    if request.method == 'POST':
            is_mcq = 'is_mcq' in request.POST

            if not selected_module.year_long:
                sem = selected_module.sem
            else:
                sem = request.POST.get('sem')

            question = Question(
                module=selected_module,
                sem=sem,
                question=request.POST.get('question'),
                answer=None if is_mcq else request.POST.get('answer'),
                is_mcq=is_mcq,
                added_by=request.user
            )
            question.save()

            if is_mcq:
                # Add new options
                options = request.POST.getlist('options[]')
                correct_options = request.POST.get('correct_options[]')
                for i, option_text in enumerate(options):
                    Option.objects.create(
                        question=question,
                        option=option_text,
                        correct=(str(i) in correct_options)
                    )
            return redirect('add_question')

    return render(request, 'add_question.html', {
        "selected_module": selected_module,
        "all_modules": all_modules,
        "semesters": Sem.choices,
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('edit_profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    now = timezone.now()
    now_date = now.date()
    claimed_today = hours_left = False
    if request.user.profile.streak:
        diff_days = (now_date - request.user.profile.last_streak).days
        if diff_days < 1:
            claimed_today = True
        if diff_days < 2:
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
            hours_left = int((end_of_day - now).total_seconds() // 3600)
        else:
            request.user.profile.reset_streak()

    return render(request, 'edit_profile.html', {
        'form': form,
        'claimed_today': claimed_today,
        'hours_left': hours_left,
    })

def leaderboard(request):
    users = Profile.objects.filter(streak__gte=1).order_by('-streak')
    return render(request, 'leaderboard.html', {'students': users})


def view_question(request, question_id):
    pass

def get_saves(request):
    return render(request, 'saved.html', {})

# to-do:
# upvote answer
# bookmark question
# add answer

# flashcard ui