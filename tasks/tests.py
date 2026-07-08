from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import CategoryForm, TaskForm
from .models import Category, Task


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anas", password="testpass123")

    def test_task_str_returns_title(self):
        task = Task.objects.create(title="Buy milk", owner=self.user)
        self.assertEqual(str(task), "Buy milk")

    def test_tasks_ordered_by_due_date(self):
        task_later = Task.objects.create(title="...", due_date="2026-08-01", owner=self.user)
        task_sooner = Task.objects.create(title="...", due_date="2026-07-10", owner=self.user)
        task_middle = Task.objects.create(title="...", due_date="2026-07-20", owner=self.user)

        tasks = Task.objects.all()

        self.assertEqual(list(tasks), [task_sooner, task_middle, task_later])

    def test_completed_at_set_when_status_becomes_completed(self):
        task = Task.objects.create(title="Ship feature", owner=self.user)
        self.assertIsNone(task.completed_at)

        task.status = Task.Status.COMPLETED
        task.save()

        self.assertIsNotNone(task.completed_at)

    def test_completed_at_cleared_when_task_reopened(self):
        task = Task.objects.create(title="Ship feature", owner=self.user, status=Task.Status.COMPLETED)
        self.assertIsNotNone(task.completed_at)

        task.status = Task.Status.PENDING
        task.save()

        self.assertIsNone(task.completed_at)

    def test_is_overdue_true_for_past_due_incomplete_task(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        task = Task.objects.create(title="Late task", owner=self.user, due_date=yesterday)
        self.assertTrue(task.is_overdue)

    def test_is_overdue_false_when_completed(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        task = Task.objects.create(
            title="Late but done", owner=self.user, due_date=yesterday, status=Task.Status.COMPLETED
        )
        self.assertFalse(task.is_overdue)

    def test_is_overdue_false_without_due_date(self):
        task = Task.objects.create(title="No due date", owner=self.user)
        self.assertFalse(task.is_overdue)


class CategoryModelTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="alice", password="testpass123")
        self.user_b = User.objects.create_user(username="bob", password="testpass123")

    def test_category_str_returns_name(self):
        category = Category.objects.create(name="Work", owner=self.user_a)
        self.assertEqual(str(category), "Work")

    def test_same_name_allowed_for_different_owners(self):
        Category.objects.create(name="Work", owner=self.user_a)
        # Should not raise — the uniqueness constraint is scoped per owner.
        Category.objects.create(name="Work", owner=self.user_b)
        self.assertEqual(Category.objects.filter(name="Work").count(), 2)


class TaskListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anas", password="testpass123")

    def test_anonymous_user_redirected_from_task_list(self):
        response = self.client.get(reverse("task-list"))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_redirected_to_expected_URL(self):
        response = self.client.get(reverse("task-list"))
        expected_path = reverse("login") + "?next=" + reverse("task-list")
        self.assertRedirects(response, expected_path)


class TaskAccessControlTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="alice", password="testpass123")
        self.user_b = User.objects.create_user(username="bob", password="testpass123")
        self.task_owned_by_b = Task.objects.create(title="Bob's secret task", owner=self.user_b)

    def test_user_cannot_view_another_users_task(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("task-detail", args=[self.task_owned_by_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_user_can_view_his_task(self):
        self.client.force_login(self.user_b)
        response = self.client.get(reverse("task-detail", args=[self.task_owned_by_b.pk]))
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_update_another_users_task(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("task-update", args=[self.task_owned_by_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_task(self):
        self.client.force_login(self.user_a)
        response = self.client.post(reverse("task-delete", args=[self.task_owned_by_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(pk=self.task_owned_by_b.pk).exists())

    def test_user_cannot_toggle_another_users_task(self):
        self.client.force_login(self.user_a)
        response = self.client.post(reverse("task-toggle", args=[self.task_owned_by_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.task_owned_by_b.refresh_from_db()
        self.assertEqual(self.task_owned_by_b.status, Task.Status.PENDING)

    def test_task_list_only_shows_own_tasks(self):
        Task.objects.create(title="Alice's task", owner=self.user_a)
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("task-list"))
        titles = [task.title for task in response.context["tasks"]]
        self.assertIn("Alice's task", titles)
        self.assertNotIn("Bob's secret task", titles)


class CategoryAccessControlTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="alice", password="testpass123")
        self.user_b = User.objects.create_user(username="bob", password="testpass123")
        self.category_owned_by_b = Category.objects.create(name="Personal", owner=self.user_b)

    def test_user_cannot_update_another_users_category(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("category-update", args=[self.category_owned_by_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_category(self):
        self.client.force_login(self.user_a)
        response = self.client.post(reverse("category-delete", args=[self.category_owned_by_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(pk=self.category_owned_by_b.pk).exists())

    def test_category_list_only_shows_own_categories(self):
        Category.objects.create(name="Work", owner=self.user_a)
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("category-list"))
        names = [category.name for category in response.context["categories"]]
        self.assertIn("Work", names)
        self.assertNotIn("Personal", names)

    def test_task_form_category_choices_scoped_to_user(self):
        Category.objects.create(name="Work", owner=self.user_a)
        form = TaskForm(user=self.user_a)
        category_ids = set(form.fields["category"].queryset.values_list("pk", flat=True))
        self.assertNotIn(self.category_owned_by_b.pk, category_ids)


class TaskFilterSearchSortTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anas", password="testpass123")
        self.client.force_login(self.user)
        self.work = Category.objects.create(name="Work", owner=self.user)
        self.today = timezone.localdate()

        self.overdue_task = Task.objects.create(
            title="Overdue report", owner=self.user, due_date=self.today - timedelta(days=2),
            priority=Task.Priority.HIGH, category=self.work,
        )
        self.completed_task = Task.objects.create(
            title="Finished setup", owner=self.user, status=Task.Status.COMPLETED,
            priority=Task.Priority.LOW,
        )
        self.pending_task = Task.objects.create(
            title="Write docs", owner=self.user, priority=Task.Priority.MEDIUM,
        )

    def test_search_matches_title(self):
        response = self.client.get(reverse("task-list"), {"q": "docs"})
        titles = [task.title for task in response.context["tasks"]]
        self.assertEqual(titles, ["Write docs"])

    def test_filter_by_status(self):
        response = self.client.get(reverse("task-list"), {"status": "completed"})
        titles = [task.title for task in response.context["tasks"]]
        self.assertEqual(titles, ["Finished setup"])

    def test_filter_by_priority(self):
        response = self.client.get(reverse("task-list"), {"priority": "high"})
        titles = [task.title for task in response.context["tasks"]]
        self.assertEqual(titles, ["Overdue report"])

    def test_filter_by_category(self):
        response = self.client.get(reverse("task-list"), {"category": self.work.pk})
        titles = [task.title for task in response.context["tasks"]]
        self.assertEqual(titles, ["Overdue report"])

    def test_filter_overdue_only(self):
        response = self.client.get(reverse("task-list"), {"overdue": "1"})
        titles = [task.title for task in response.context["tasks"]]
        self.assertEqual(titles, ["Overdue report"])

    def test_sort_priority_orders_high_to_low(self):
        response = self.client.get(reverse("task-list"), {"sort": "priority"})
        titles = [task.title for task in response.context["tasks"]]
        self.assertEqual(titles, ["Overdue report", "Write docs", "Finished setup"])

    def test_dashboard_stats(self):
        response = self.client.get(reverse("task-list"))
        stats = response.context["stats"]
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["pending"], 2)
        self.assertEqual(stats["overdue"], 1)


class TaskQuickCompleteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anas", password="testpass123")
        self.client.force_login(self.user)
        self.task = Task.objects.create(title="Write report", owner=self.user)

    def test_toggle_marks_pending_task_completed(self):
        self.client.post(reverse("task-toggle", args=[self.task.pk]))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(self.task.completed_at)

    def test_toggle_reopens_completed_task(self):
        self.task.status = Task.Status.COMPLETED
        self.task.save()

        self.client.post(reverse("task-toggle", args=[self.task.pk]))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.PENDING)
        self.assertIsNone(self.task.completed_at)

    def test_toggle_requires_post(self):
        response = self.client.get(reverse("task-toggle", args=[self.task.pk]))
        self.assertEqual(response.status_code, 405)

    def test_toggle_ignores_unsafe_next_redirect(self):
        response = self.client.post(
            reverse("task-toggle", args=[self.task.pk]), {"next": "https://evil.example.com/"}
        )
        self.assertRedirects(response, reverse("task-list"))


class TaskCrudViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anas", password="testpass123")
        self.client.force_login(self.user)

    def test_create_task_sets_owner(self):
        response = self.client.post(reverse("task-create"), {
            "title": "New task", "description": "", "priority": "medium",
            "status": "pending", "category": "", "due_date": "",
        })
        self.assertRedirects(response, reverse("task-list"))
        task = Task.objects.get(title="New task")
        self.assertEqual(task.owner, self.user)

    def test_update_task(self):
        task = Task.objects.create(title="Old title", owner=self.user)
        response = self.client.post(reverse("task-update", args=[task.pk]), {
            "title": "New title", "description": "", "priority": "high",
            "status": "pending", "category": "", "due_date": "",
        })
        self.assertRedirects(response, reverse("task-list"))
        task.refresh_from_db()
        self.assertEqual(task.title, "New title")
        self.assertEqual(task.priority, "high")

    def test_delete_task(self):
        task = Task.objects.create(title="Delete me", owner=self.user)
        response = self.client.post(reverse("task-delete", args=[task.pk]))
        self.assertRedirects(response, reverse("task-list"))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())


class CategoryCrudViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anas", password="testpass123")
        self.client.force_login(self.user)

    def test_create_category_sets_owner(self):
        response = self.client.post(reverse("category-create"), {"name": "Work"})
        self.assertRedirects(response, reverse("category-list"))
        category = Category.objects.get(name="Work")
        self.assertEqual(category.owner, self.user)

    def test_delete_category_unassigns_tasks_instead_of_deleting_them(self):
        category = Category.objects.create(name="Work", owner=self.user)
        task = Task.objects.create(title="Task in category", owner=self.user, category=category)

        self.client.post(reverse("category-delete", args=[category.pk]))

        task.refresh_from_db()
        self.assertIsNone(task.category)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())


class TaskFormValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anas", password="testpass123")

    def test_blank_title_rejected(self):
        form = TaskForm(data={"title": "   ", "priority": "medium", "status": "pending"}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


class CategoryFormValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anas", password="testpass123")

    def test_duplicate_category_name_rejected(self):
        Category.objects.create(name="Work", owner=self.user)
        form = CategoryForm(data={"name": "work"}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_updating_own_category_without_changing_name_is_valid(self):
        category = Category.objects.create(name="Work", owner=self.user)
        form = CategoryForm(data={"name": "Work"}, instance=category, user=self.user)
        self.assertTrue(form.is_valid())
