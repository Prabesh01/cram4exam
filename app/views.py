from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import ProfileForm
from django.db.models import Q
from django.http import JsonResponse
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.models import User

from app.models import Module, Sem, Year, Question, Option, Profile, UserAnswer, DailyQuestion, Bookmark, Upvote, GroupCousework, Team, TeamMembership, Designation, Role
from django.utils import timezone
from datetime import timedelta
from datetime import datetime, time

from collections import defaultdict

def generate_daily_questions(user):
    existing_questions = DailyQuestion.objects.filter(user=user).values_list('question', flat=True)

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
    questions=questions.order_by('-added_by__profile__legit','-date_added').prefetch_related('option_set','added_by__profile')
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

    is_mcq=sem=no_two=None
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
                answer=request.POST.get('answer'),
                is_mcq=is_mcq,
                added_by=request.user
            )
            question.save()

            if is_mcq:
                option_ids = request.POST.getlist('option_ids[]')
                options = request.POST.getlist('options[]')
                correct_option_ids = request.POST.getlist('correct_option_ids[]')

                # if option 0 is empty, its value shall be "True" by default
                if options[0].strip() == '':
                    options[0] = 'True'
                if options[1].strip() == '':
                    options[1] = 'False'
                if len(options)>3 and options[3].strip() == '':
                    options[3] = 'None of the above'
                if len(options)>2:
                    no_two=True
                    for i in range(len(options) - 1, 1, -1):
                        if options[i].strip() == '':
                            del options[i]
                            del option_ids[i]

                options = dict(zip(option_ids,options))

                for id, option_text in options.items():
                    Option.objects.create(
                        question=question,
                        option=option_text,
                        correct=(id in correct_option_ids)
                    )

            # request.session['successMessage'] = "Question added successfully"
            # return redirect('add_question')
            messages.add_message(request, messages.SUCCESS, "Question added successfully!")

    return render(request, 'add_question.html', {
        "selected_module": selected_module,
        "all_modules": all_modules,
        "semesters": Sem.choices,
        "is_mcq": is_mcq, "no_two": no_two, "sem": sem
    })

@login_required
def edit_profile(request):
    profile=request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            generate_daily_questions(request.user)
            return redirect('edit_profile')
    else:
        form = ProfileForm(instance=profile)
    now = timezone.now()
    now_date = now.date()
    claimed_today = hours_left = False
    if profile.streak:
        diff_days = (now_date - profile.last_streak).days
        if diff_days < 1:
            claimed_today = True
        if diff_days < 2:
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
            hours_left = int((end_of_day - now).total_seconds() // 3600)
        else:
            profile.reset_streak()

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
            #if not question.is_mcq:
            if True:
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
            'is_upvoted': is_upvoted,
            'is_users_answer': answer.user == request.user
        })

    answer_data.sort(
        key=lambda x: (
            not x['is_users_answer'],
            -x['upvote_count'],
            -x['answer'].date_answered.timestamp() if x['answer'].date_answered else 0
        )
    )


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

    grouped_answers = defaultdict(list)
    for answer in answers:
        grouped_answers[answer.question].append(answer)

    return render(request, 'saved.html', {'grouped_answers': dict(grouped_answers),'questions': questions, 'bookmarks': bookmarks})

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
            question.answer = request.POST.get('answer')
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
            request.session['successMessage'] = "Question Updated successfully"
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

@login_required
def cwteam(request):
    selected_gcid = request.GET.get('gcid') or request.POST.get('gcid')
    grp_courseworks = GroupCousework.objects.filter(
        Q(module__sem=request.user.profile.sem) | Q(module__year_long=True),
        Q(module__year=request.user.profile.year)
    )
    user_team=user_role=None
    if not selected_gcid:
        return render(request, 'cwteam.html', {'userteam': None, 'grp_courseworks': grp_courseworks})

    selected_gcid = int(selected_gcid)

    section_filter = request.GET.get('section')

    current_year = timezone.now().year

    membership = TeamMembership.objects.filter(user=request.user, team__group_coursework__gcid=selected_gcid, team__created_at__year=current_year).select_related('team').first()
    if membership:
        user_team = membership.team
    else:
        user_role=Designation.objects.filter(user=request.user,group_coursework__gcid=selected_gcid, created_at__year=current_year)

    teams = []
    teams_query = Team.objects.filter(group_coursework__gcid=selected_gcid, created_at__year=current_year)

    users_looking_for_team = Designation.objects.filter(group_coursework__gcid=selected_gcid, created_at__year=current_year)

    only_my_section = request.POST.get('only_my_section') == 'on'
    if only_my_section:
        user_section = request.user.profile.section
        teams_query = teams_query.filter(teammembership__user__profile__section=user_section).distinct()
        users_looking_for_team = users_looking_for_team.filter(user__profile__section=user_section)

    teams = teams_query.prefetch_related('teammembership_set__user')

    return render(request, 'cwteam.html', {'userteam': user_team, 'grp_courseworks': grp_courseworks, 'selected_gcid': selected_gcid, 'teams': teams, 'current_section': section_filter, "roles": Role.choices, "user_role":user_role, "users_looking_for_team":users_looking_for_team, 'only_my_section': only_my_section})

def set_cw_status(request):
    selected_gcid = int(request.POST.get('gcid'))
    selected_role = request.POST.get('open_for')
    return_url = f"{reverse('cwteam')}?gcid={selected_gcid}"
    if selected_gcid and selected_role:
        group_coursework = get_object_or_404(GroupCousework, gcid=selected_gcid)
        existing_designation = Designation.objects.filter(user=request.user, group_coursework=group_coursework).first()
        if existing_designation:
            if existing_designation.open_for == selected_role:
                existing_designation.delete()
                return redirect(return_url)
        Designation.objects.update_or_create(
            user=request.user,
            group_coursework=group_coursework,
            defaults={'open_for': selected_role}
        )
        return redirect(return_url)
    
@login_required
def create_team(request):
    if request.method != 'POST':
        return redirect('cwteam')

    gcid = request.POST.get('gcid')
    team_name = request.POST.get('team_name', '').strip()
    looking_for = request.POST.get('looking_for') or None

    if not gcid or not team_name:
        messages.add_message(request, messages.WARNING, "Team name is required!")
        return redirect(f'/cwteam/?gcid={gcid}')

    gc = get_object_or_404(GroupCousework, gcid=gcid)

    # Prevent user from being in multiple teams for the same coursework
    already_in = TeamMembership.objects.filter(
        user=request.user,
        team__group_coursework=gc
    ).exists()
    if already_in:
        messages.add_message(request, messages.WARNING, 'You are already in a team for this coursework.')
        return redirect(f'/cwteam/?gcid={gcid}')

    team = Team.objects.create(
        user=request.user,
        name=team_name,
        group_coursework=gc,
        looking_for=looking_for,
    )

    # Add creator as first member
    creator_role = request.POST.getlist('new_member_role')
    creator_role_value = creator_role[0] if creator_role else None
    TeamMembership.objects.create(team=team, user=request.user, position=creator_role_value)
    # remove any open designation for this coursework since user is now in a team
    Designation.objects.filter(user=request.user, group_coursework=gc).delete()

    # Add additional members from the second member row
    emails = request.POST.getlist('new_member_email')
    roles = request.POST.getlist('new_member_role')

    # Skip index 0 (creator's disabled field), process from index 1
    for email, role in zip(emails[1:], roles[1:]):
        email = email.strip()
        if not email:
            continue
        try:
            member = User.objects.get(email=email)
            if member == request.user:
                continue
            already_in_any = TeamMembership.objects.filter(
                user=member,
                team__group_coursework=gc
            ).exists()
            if already_in_any:
                messages.add_message(request, messages.WARNING, f'{email} is already in another team.')
                continue
            TeamMembership.objects.create(team=team, user=member, position=role or None)
            Designation.objects.filter(user=request.user, group_coursework=gc).delete()
        except User.DoesNotExist:
            messages.add_message(request, messages.WARNING, f'No user found with email {email}.')

    messages.success(request, 'Team created successfully.')
    return redirect(f'/cwteam/?gcid={gcid}')


@login_required
def update_team(request, team_id):
    if request.method != 'POST':
        return redirect('cwteam')

    team = get_object_or_404(Team, id=team_id)
    gcid = team.group_coursework.gcid

    is_owner = team.user == request.user

    if not is_owner:
        messages.error(request, 'Only team owner can update the team.')
        return redirect(f'/cwteam/?gcid={gcid}')

    team_name = request.POST.get('team_name', '').strip()
    looking_for = request.POST.get('looking_for') or None
    if team_name:
        team.name = team_name
    team.looking_for = looking_for
    team.save()

    # Update roles for existing members
    for membership in team.teammembership_set.all():
        role_key = f'role_{membership.user.id}'
        new_role = request.POST.get(role_key) or None
        membership.position = new_role
        membership.save()

    # Add new member if provided
    new_email = request.POST.get('new_member_email', '').strip()
    new_role = request.POST.get('new_member_role') or None
    if new_email:
        try:
            new_user = User.objects.get(email=new_email)
            already_in = TeamMembership.objects.filter(
                user=new_user,
                team__group_coursework=team.group_coursework
            ).exists()
            if already_in:
                messages.warning(request, f'{new_email} is already in a team.')
            else:
                TeamMembership.objects.create(team=team, user=new_user, position=new_role)
                Designation.objects.filter(user=request.user, group_coursework=team.group_coursework).delete()
                messages.success(request, f'{new_email} added to the team.')
        except User.DoesNotExist:
            messages.warning(request, f'No user found with email {new_email}.')

    messages.success(request, 'Team updated.')
    return redirect(f'/cwteam/?gcid={gcid}')


@login_required
def kick_member(request, team_id, user_id):
    team = get_object_or_404(Team, id=team_id)
    gcid = team.group_coursework.gcid

    if team.user != request.user:
        messages.error(request, 'Only the team owner can remove members.')
        return redirect(f'/cwteam/?gcid={gcid}')

    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        messages.error(request, 'Use "Leave Team" to remove yourself.')
        return redirect(f'/cwteam/?gcid={gcid}')

    TeamMembership.objects.filter(team=team, user=target_user).delete()
    messages.success(request, f'{target_user.username} has been removed from the team.')
    return redirect(f'/cwteam/?gcid={gcid}')


@login_required
def leave_team(request, team_id):
    if request.method != 'POST':
        return redirect('cwteam')

    team = get_object_or_404(Team, id=team_id)
    gcid = team.group_coursework.gcid

    is_member = TeamMembership.objects.filter(team=team, user=request.user).exists()
    if not is_member:
        messages.error(request, 'You are not in this team.')
        return redirect(f'/cwteam/?gcid={gcid}')

    if team.user == request.user:
        # Owner disbands the entire team
        team.delete()  # cascades to TeamMembership
        messages.success(request, 'Team has been disbanded.')
    else:
        # Non-owner just leaves
        TeamMembership.objects.filter(team=team, user=request.user).delete()
        messages.success(request, 'You have left the team.')

    return redirect(f'/cwteam/?gcid={gcid}')
