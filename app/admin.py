from django.contrib import admin
from .models import Module, Question, Option, DailyQuestion, UserAnswer, Profile, Bookmark, Upvote

class OptionInline(admin.TabularInline):
    model = Option
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('qid', 'module', 'question', 'is_mcq', 'is_archived')
    list_filter = ('module', 'is_mcq', 'is_archived')
    search_fields = ('question', 'module__name', 'module__code')
    inlines = [OptionInline]

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'year', 'sem', 'year_long')
    list_filter = ('year', 'sem', 'year_long')
    search_fields = ('code', 'name')

admin.site.register(Module, ModuleAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(DailyQuestion)
admin.site.register(UserAnswer)
admin.site.register(Profile)
admin.site.register(Bookmark)
admin.site.register(Upvote)
