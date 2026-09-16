from django.contrib import admin
from .models import *

admin.site.register(ClassRoom)
admin.site.register(Subject)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(Grade)
admin.site.register(WeeklyRating)
admin.site.register(News)
admin.site.register(Event)


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'role', 'classroom', 'is_used', 'created_at')
    list_filter = ('role', 'is_used')
    search_fields = ('code',)
    readonly_fields = ('created_at',)
    fields = ('code', 'role', 'classroom', 'is_used')