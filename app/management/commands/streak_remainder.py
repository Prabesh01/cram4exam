# digital ocean blocks smtp by default in their droplets!!
# using zohomail api: https://www.zoho.com/mail/help/api/post-send-an-email.html
# 0 13 * * * /home/prabesh/cram4exam/venv/bin/python3 /home/prabesh/cram4exam/manage.py streak_remainder

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

env_file=BASE_DIR / ".env"
load_dotenv(env_file)

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, time

import smtplib
import requests
import json

User = get_user_model()

zoho_refresh_token_url = f"https://accounts.zoho.com/oauth/v2/token?refresh_token={os.getenv('zoho_refresh_token')}&grant_type=refresh_token&client_id={os.getenv('zoho_clientid')}&client_secret={os.getenv('zoho_client_secret')}"
access_token=requests.post(zoho_refresh_token_url).json()["access_token"]
print(access_token)
zoho_send_mail_url=f"https://mail.zoho.com/api/accounts/{os.getenv('zoho_accountid')}/messages"
headers={"Authorization": "Zoho-oauthtoken "+access_token}

class Command(BaseCommand):
    help = 'Sends streak reminder emails to users who might lose their streak'

    def handle(self, *args, **options):
        now = timezone.now()
        now_date = now.date()
        
        # Get users with active streaks
        users = User.objects.filter(profile__streak__gt=0)
        
        for user in users:
            if user.profile.last_streak:
                diff_days = (now_date - user.profile.last_streak).days

                if diff_days < 2 and diff_days >= 1:  # User has less than 24 hours to maintain streak

                    print(f"Sending remainder email to {user.email}..")

                    # Calculate hours left until midnight
                    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
                    hours_left = int((end_of_day - now).total_seconds() // 3600)
                    
                    # Send reminder email
                    subject = f"[RATTA] Don't lose your {user.profile.streak}-day streak!"
                    message = (
                        f"Hi {user.username},\n\n"
                        f"You're on a {user.profile.streak}-day streak, That's amazing!"
                        f"You have {hours_left} hours left to maintain it.\n\n"
                        "Let's study a little everyday. Don't break the chain!\n\n"
                        "ratta.cote.ws Team"
                    )

                    html_message = f"""
                    <p>Hi {user.first_name},</p>
                    <p>You're on a {user.profile.streak}-day streak, that's amazing! 🌟<br>
                    This is a gentle remainder that you have {hours_left} hours left to maintain it.</p>
                
                    <a href="{os.getenv('web_url')}" 
                       style="background-color: #4CAF50; 
                              border: none;
                              color: white;
                              padding: 15px 32px;
                              text-align: center;
                              text-decoration: none;
                              display: inline-block;
                              font-size: 16px;
                              margin: 10px 0;
                              cursor: pointer;
                              border-radius: 4px;">
                        Continue My Streak
                    </a>
                    
                    <p>Let's study a little everyday. Don't break the chain!</p>
                    <p>- ratta.cote.ws Team</p>
                    """

                    #with smtplib.SMTP(os.getenv('smtp_host'), os.getenv('smtp_port')) as server:
                    #    server.starttls()
                    #    server.login(os.getenv('smtp_user'), os.getenv('smtp_password'))
                    #    #message = f"Subject: {subject}\n\n{html_message}"
                    #    server.sendmail(os.getenv('smtp_sender'), user.email, message)

                    data={"fromAddress":os.getenv('smtp_sender'), "toAddress": user.email,"subject":subject, "content":html_message, "askReceipt" : "yes"}
                    requests.post(zoho_send_mail_url,headers=headers,json=data)
