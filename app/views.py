from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from django.db.models import Q
from django.http import JsonResponse
from django.db.models import Count

from app.models import Module, Sem, Year, Question, Option, Profile, UserAnswer, DailyQuestion, Bookmark, Upvote
from django.utils import timezone
from datetime import timedelta
from datetime import datetime, time

def generate_daily_questions(user):
    existing_questions = DailyQuestion.objects.filter(user=user, status=False).values_list('question', flat=True)

    if user.profile.sem == Sem.TWO:
        questions = Question.objects.filter(
            Q(module__sem=user.profile.sem) | Q(module__year_long=True),
            Q(module__year=user.profile.year),
            ~Q(added_by__username="bot")
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
        questions = Question.objects.filter(~Q(added_by__username="bot"),module__code=code).order_by('date_added')
    else:
        questions = Question.objects.filter(~Q(added_by__username="bot"),module__code=code, sem=Sem.ONE).order_by('date_added')
    questions=questions.order_by('date_added').prefetch_related('option_set')
    return render(request, 'qbank.html', {'module': module,'questions':questions})

@login_required
def flash_cards(request):
    if request.method == 'POST' and 'bookmark_question' in request.POST:
        question_id = request.POST.get('bookmark_question')
        question = get_object_or_404(Question, qid=question_id)

        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            question=question
        )
        if not created:
            bookmark.delete()

    modules = Module.objects.filter(Q(sem=request.user.profile.sem) | Q(year_long=True), year=request.user.profile.year)

    questions= None
    selected_module = request.GET.get('module')
    if not selected_module: selected_module = 'all'
    if selected_module:
        if selected_module == 'all':
            if request.user.profile.sem == Sem.TWO:
                questions = Question.objects.filter(added_by__username="bot",module__in=modules).order_by('?')
            else:
                questions = Question.objects.filter(added_by__username="bot",module__in=modules, sem=Sem.ONE).order_by('?')
        else:
            selected_module = get_object_or_404(Module, code=selected_module)

            if request.user.profile.sem == Sem.TWO:
                questions = Question.objects.filter(added_by__username="bot",module=selected_module).order_by('?')
            else:
                questions = Question.objects.filter(added_by__username="bot",module=selected_module, sem=Sem.ONE).order_by('?')

    questions_data=[]
    for question in questions:
        has_bookmark = Bookmark.objects.filter(
            user=request.user,
            question=question
        ).exists()

        questions_data.append({
            'question': question,
            'has_bookmark': has_bookmark
        })


    return render(request, 'flash_cards.html', {'modules': modules,'questions':questions_data, 'selected_module': selected_module})

@login_required
def add_question(request):

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

            request.session['successMessage'] = "Question added successfully"
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

@login_required
def view_question(request, question_id):
    question = get_object_or_404(Question, qid=question_id)

    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(
            user=request.user,
            question=question
        ).exists()

    if request.method == 'POST':
        if 'text_answer' in request.POST:
            answer = request.POST.get('text_answer')
            # save answer
            if not question.is_mcq:
                UserAnswer.objects.create(
                    user=request.user,
                    question=question,
                    answer=answer
                )
        elif 'upvote_answer' in request.POST:
            answer_id = request.POST.get('upvote_answer')
            answer = get_object_or_404(UserAnswer, pk=answer_id)

            upvote, created = Upvote.objects.get_or_create(
                user=request.user,
                answer=answer
            )
            if not created:
                upvote.delete()
        elif 'bookmark_question' in request.POST:
            bookmark, created = Bookmark.objects.get_or_create(
                user=request.user,
                question=question
            )
            if not created:
                bookmark.delete()
        return redirect('view_question', question_id=question_id)
    answers = UserAnswer.objects.filter(question=question).order_by('-date_answered')

    answer_data = []
    for answer in answers:
        upvote_count = Upvote.objects.filter(answer=answer).count()
        is_upvoted = False
        if request.user.is_authenticated:
            is_upvoted = Upvote.objects.filter(
                user=request.user,
                answer=answer
            ).exists()

        answer_data.append({
            'answer': answer,
            'upvote_count': upvote_count,
            'is_upvoted': is_upvoted
        })

    return render(request, 'question.html', {
        'question': question,
        'answers': answer_data,
        'is_bookmarked': is_bookmarked
    })

@login_required
def get_saves(request):
    answers = UserAnswer.objects.filter(user=request.user).order_by('-date_answered')
    questions = Question.objects.filter(added_by=request.user).order_by('-date_added')
    bookmarks = Bookmark.objects.filter(user=request.user).order_by('-date_bookmarked')
    return render(request, 'saved.html', {'answers': answers,'questions': questions, 'bookmarks': bookmarks})

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, qid=question_id, added_by=request.user)
    question.delete()

    return redirect('saves')

@login_required
def delete_answer(request, answer_id):
    answer = get_object_or_404(UserAnswer, pk=answer_id, user=request.user)
    answer.delete()

    return redirect('saves')

@login_required
def edit_question(request, qid):
    question = get_object_or_404(Question, qid=qid, added_by=request.user)

    if request.method == 'POST':
            is_mcq = 'is_mcq' in request.POST

            if not question.module.year_long:
                sem = question.module.sem
            else:
                sem = request.POST.get('sem')

            # Update the question
            question.question = request.POST.get('question')
            question.answer = None if is_mcq else request.POST.get('answer')
            question.is_mcq = is_mcq
            question.sem = sem
            question.save()

            if is_mcq:
                # delete old options
                Option.objects.filter(question=question).delete()
                # Add new options
                options = request.POST.getlist('options[]')
                correct_options = request.POST.get('correct_options[]')
                for i, option_text in enumerate(options):
                    Option.objects.create(
                        question=question,
                        option=option_text,
                        correct=(str(i) in correct_options)
                    )
            return redirect('saves')

    return render(request, 'edit_question.html', {'question': question, 'semesters': Sem.choices})

@login_required
def edit_answer(request, answer_id):
    answer = get_object_or_404(UserAnswer, pk=answer_id, user=request.user)

    answer.answer = request.POST.get('text_answer')
    answer.save()
    return redirect('saves')

@login_required
def top_answers(request, question_id):
    question = get_object_or_404(Question, qid=question_id)
    answers = UserAnswer.objects.filter(question=question).order_by('-date_answered')
    self_answers = UserAnswer.objects.filter(question=question, user=request.user).order_by('-date_answered')

    top_answer = answers.annotate(upvote_count=Count('upvote')).filter(upvote_count__gte=2).order_by('-upvote_count').first()

    self_answers = [a.answer for a in self_answers]
    top_answer = top_answer.answer if top_answer else None

    return JsonResponse({'self_answers': self_answers, 'top_answer': top_answer})

# to-do:
# view question
# bookmark/undo question
# upvote/undo answer

