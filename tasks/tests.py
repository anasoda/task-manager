from django.test import TestCase
from django.contrib.auth.models import User
from .models import Task
from django.urls import reverse

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

        # tasks[0] should be the one with the EARLIEST due_date, tasks[-1] the latest.
        # Write an assertEqual comparing the actual queryset order
        # to the order you expect: [task_sooner, task_middle, task_later]
        self.assertEqual(list(tasks), [task_sooner, task_middle, task_later])   

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