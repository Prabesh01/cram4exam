from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Sem(models.IntegerChoices):
    ONE = 1, 'semester 1'
    TWO = 2, 'semester 2'

class Year(models.IntegerChoices):
    ONE = 1, 'year 1'
    TWO = 2, 'year 2'
    THREE = 3, 'year 3'

class Module(models.Model):

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    year_long = models.BooleanField(default=False)
    year = models.IntegerField(choices=Year.choices, default=Year.ONE)
    sem = models.IntegerField(choices=Sem.choices, default=Sem.ONE)

    def __str__(self):
        return self.name

class Question(models.Model):
    qid = models.AutoField(primary_key=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    sem = models.IntegerField(choices=Sem.choices, default=Sem.ONE)
    question = models.TextField()
    is_mcq = models.BooleanField(default=False)
    answer = models.TextField(null=True, blank=True)
    added_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.question

    # get options
    def get_options(self):
        return Option.objects.filter(question=self)

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.TextField()
    correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option

class DailyQuestion(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)

class UserAnswer(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField(null=True, blank=True)
    date_answered = models.DateTimeField(auto_now_add=True)


class SavedQuestion(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    date_saved = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    streak = models.IntegerField(default=0)
    last_streak = models.DateField(null=True, blank=True)
    year = models.IntegerField(choices=Year.choices, null=True, blank=True)
    sem = models.IntegerField(choices=Sem.choices, null=True, blank=True)
    legit = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def add_streak(self):
        today = timezone.now().date()

        if self.last_streak:
            diff_days = (today - self.last_streak).days
            if diff_days == 1:
                self.streak += 1
            elif diff_days > 1:
                self.streak = 1
            else: return
        else:
            self.streak = 1

        self.last_streak = today
        self.save()

    def reset_streak(self):
        today = timezone.now().date()

        if self.last_streak:
            diff_days = (today - self.last_streak).days
            if diff_days > 1:
                self.streak = 0

                self.save()

class Bookmark(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    date_bookmarked = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.question.question}"

class Upvote(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    answer = models.ForeignKey(UserAnswer, on_delete=models.CASCADE)
    date_upvoted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.answer.answer}"
