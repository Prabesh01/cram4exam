from django.shortcuts import redirect, render

import os
from pathlib import Path
from dotenv import load_dotenv

from django.contrib.auth import login as l
from django.contrib.auth.models import User
from app.models import Profile

import requests, json
from datetime import datetime

import google_auth_oauthlib.flow

BASE_DIR = Path(__file__).resolve().parent.parent

env_file=BASE_DIR / ".env"
load_dotenv(env_file)

client_config = {
    "web": {
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}
flow = google_auth_oauthlib.flow.Flow.from_client_config(
    client_config,
    scopes=['openid','https://www.googleapis.com/auth/userinfo.email','https://www.googleapis.com/auth/userinfo.profile'])

flow.redirect_uri = os.getenv('web_url')+'/auth/login/callback/'

def login(request):
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        hd='icp.edu.np',
    )
    return render(request,'login.html',{"url":authorization_url})

def callback(request):
    if 'code' not in request.GET:
        return redirect('login')
    flow.fetch_token(code=request.GET['code'])
    credentials = json.loads(flow.credentials.to_json())
    r=requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers={"Authorization":"Bearer "+credentials['token']})
    if r.status_code != 200:
        authorization_url, state = flow.authorization_url(
            access_type='offline',
        )
        return redirect('login')
    email_addr = r.json()['email'].lower().strip()
    email_name, _ = email_addr.rsplit('@', 1)

    year, sem = get_year_sem(email_name)
    if not year: return redirect('login')

    names=email_name.split('.')[:-1]

    fname=' '.join(names[:-1]).title()
    lname=names[-1].title()

    user, created = User.objects.get_or_create(username=email_name, first_name=fname, last_name=lname, email=email_addr)
    l(request, user)
    if created:
        Profile.objects.create(user=user, year=year, sem=sem)
    return redirect('home')

def logout(request):
    if 'user' in request.session:
        del request.session['user']
    return redirect('login')

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
