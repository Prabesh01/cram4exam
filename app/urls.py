from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add/', views.add_question, name='add_question'),
    path('view', views.list_question, name='qbank'),
    path('edit/<int:qid>/', views.add_question, name='edit_question'),
    path('question/<int:question_id>/', views.view_question, name='view_question'),
    path('modules/', views.view_modules, name='modules'),
    path('flash-cards/', views.flash_cards, name='flash_cards'),
    path('profile/', views.edit_profile, name='edit_profile'),
    path('leaderboard/', views.leaderboard, name='lb'),
    path('saved/', views.get_saves, name='saves'),
]