from django.contrib import admin
from .models import Task, Category


class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "priority", "category", "due_date", "owner"]
    list_filter = ["status", "priority", "category"]
    search_fields = ["title", "description"]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "owner"]
    search_fields = ["name"]


admin.site.register(Task, TaskAdmin)
admin.site.register(Category, CategoryAdmin)
