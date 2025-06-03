# 0 0 * * * /home/prabesh/cram4exam/venv/bin/python3 /home/prabesh/cram4exam/manage.py reset_streak

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, time

User = get_user_model()

class Command(BaseCommand):
    help = 'Resets all user\'s streak to zero at midnight if they couldn\'t maintain it.'

    def handle(self, *args, **options):
        now = timezone.now()
        now_date = now.date()

        # Get users with active streaks
        users = User.objects.filter(profile__streak__gt=0)

        for user in users:
            if user.profile.last_streak:
                diff_days = (now_date - user.profile.last_streak).days
                if diff_days >= 2: user.profile.reset_streak()

