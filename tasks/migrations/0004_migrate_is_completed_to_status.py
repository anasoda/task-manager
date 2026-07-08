from django.db import migrations
from django.utils import timezone


def forwards(apps, schema_editor):
    Task = apps.get_model("tasks", "Task")
    Task.objects.filter(is_completed=True).update(status="completed", completed_at=timezone.now())
    Task.objects.filter(is_completed=False).update(status="pending")


def backwards(apps, schema_editor):
    Task = apps.get_model("tasks", "Task")
    Task.objects.filter(status="completed").update(is_completed=True)
    Task.objects.exclude(status="completed").update(is_completed=False)


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0003_add_category_and_task_fields"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
