from django.contrib import admin
from .models import Module, Question, Option, DailyQuestion, UserAnswer, Profile, Bookmark, Upvote, GroupCousework, Team, TeamMembership, Designation

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

class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user','question__qid')

class GroupCouseworkAdmin(admin.ModelAdmin):
    list_display = ('module__code','name')

class TeanAdmin(admin.ModelAdmin):
    list_display = ('user','name','group_coursework__module__code','created_at_year')

    def created_at_year(self, obj):
        return obj.created_at.year
    created_at_year.short_description = 'Year'

class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('team','user')

class DesignationAdmin(admin.ModelAdmin):
    list_display = ('group_coursework__gcid','user')

admin.site.register(Module, ModuleAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(DailyQuestion)
admin.site.register(UserAnswer, UserAnswerAdmin)
admin.site.register(Profile)
admin.site.register(Bookmark)
admin.site.register(Upvote)

admin.site.register(GroupCousework, GroupCouseworkAdmin)
admin.site.register(Team, TeanAdmin)
admin.site.register(TeamMembership, TeamMembershipAdmin)
admin.site.register(Designation, DesignationAdmin)
