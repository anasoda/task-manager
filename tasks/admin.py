from django.contrib import admin
from .models import Task

# Register your models here.


class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "is_completed", "due_date"]
    list_filter = ["is_completed"]
    search_fields  = ["title", "description"]

admin.site.register(Task, TaskAdmin)