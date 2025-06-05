# 0 0 1 7 * /home/prabesh/cram4exam/venv/bin/python3 /home/prabesh/cram4exam/manage.py promote_year

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, time

User = get_user_model()

class Command(BaseCommand):
    help = 'Changes year and semester of users.'

    def handle(self, *args, **options):
        users = User.objects.all().exclude(profile__year=3)

        for user in users:
            year, sem = get_year_sem(user.username)
            if not year: continue
            if user.profile.year==year and user.profile.sem==sem: continue
            print(f"{user.email}: Year:{year} Sem-{sem}")
            user.profile.year=year
            user.profile.sem=sem
            user.profile.save()

def get_year_sem(email_name):
    batch = email_name.split('.')[-1]
    if len(batch)!=3 or (batch[0]!='a' and batch[0]!='s') or not batch[1:].isdigit():
        return None, None
    year = int('20'+batch[1:])
    cur_year = datetime.now().year
    cur_month = datetime.now().month

    # first year is different for a and s
    sem=0
    if batch[0]=='a':
        if year == cur_year:
            year=1
            sem=1
        elif cur_year == year+1 and cur_month<=6:
                year=1
                sem=2
    else:
        if year == cur_year and cur_month<9:
            year=1
            if cur_month<6:
                sem=1
            else:
                sem=2
    if sem:
        return year, sem

    # 2nd and 3rd year same. a23 = s24
    if batch[0]=='s':
        year = year -1

    if cur_year == year+1:
        year=2
        sem=1
    elif cur_year == year+2:
        if cur_month<=2:
            year=2
            sem=1
        elif cur_month<=6:
            year=2
            sem=2
        else:
            year=3
            sem=1
    else:
        if cur_month<=2:
            year=3
            sem=1
        else:
            year=3
            sem=2
    return year, sem
