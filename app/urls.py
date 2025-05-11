from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # answer is posted to it
    path('add/', views.add_question, name='add_question'),
    path('questions/', views.list_question, name='qbank'),
    path('edit/<int:qid>/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/', views.view_question, name='view_question'),
    path('answers/<int:question_id>/', views.top_answers, name='top_answers'),
    path('edit/<int:qid>/', views.edit_question, name='edit_question'),
    path('delete/<int:question_id>/', views.delete_question, name='delete_question'),

    path('a/edit/<int:answer_id>', views.edit_answer, name='edit_answer'),
    path('a/delete/<int:answer_id>', views.delete_answer, name='delete_answer'),

    path('modules/', views.view_modules, name='modules'),
    path('flash-cards/', views.flash_cards, name='flash_cards'),
    path('profile/', views.edit_profile, name='edit_profile'),
    path('leaderboard/', views.leaderboard, name='lb'),
    path('saved/', views.get_saves, name='saves'),
]