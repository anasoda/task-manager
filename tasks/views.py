from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField, Count, Q
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Task, Category
from .forms import TaskForm, CategoryForm

# Priority is stored as text (low/medium/high), so plain alphabetical ordering
# would sort them wrong. This maps each priority to a number we can sort by.
PRIORITY_RANK = Case(
    When(priority=Task.Priority.HIGH, then=Value(0)),
    When(priority=Task.Priority.MEDIUM, then=Value(1)),
    When(priority=Task.Priority.LOW, then=Value(2)),
    output_field=IntegerField(),
)

SORT_OPTIONS = {
    "due_date": "due_date",
    "-due_date": "-due_date",
    "priority": "priority_rank",
    "-priority": "-priority_rank",
    "created_at": "created_at",
    "-created_at": "-created_at",
}


@login_required
def task_list(request):
    owner_tasks = Task.objects.filter(owner=request.user)
    today = timezone.localdate()

    # Stats always reflect ALL of the user's tasks, independent of the
    # search/filter controls below, so the numbers don't jump around as
    # someone filters the list.
    total = owner_tasks.count()
    completed = owner_tasks.filter(status=Task.Status.COMPLETED).count()
    overdue = owner_tasks.filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED).count()
    due_today = owner_tasks.filter(due_date=today).exclude(status=Task.Status.COMPLETED).count()
    stats = {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "overdue": overdue,
        "due_today": due_today,
        "completion_percentage": round((completed / total) * 100) if total else 0,
    }

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    category_id = request.GET.get("category", "")
    overdue_only = request.GET.get("overdue") == "1"
    sort = request.GET.get("sort", "due_date")

    tasks = owner_tasks.select_related("category")
    if search:
        tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))
    if status in Task.Status.values:
        tasks = tasks.filter(status=status)
    if priority in Task.Priority.values:
        tasks = tasks.filter(priority=priority)
    if category_id.isdigit():
        tasks = tasks.filter(category_id=category_id)
    if overdue_only:
        tasks = tasks.filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED)

    tasks = tasks.annotate(priority_rank=PRIORITY_RANK).order_by(SORT_OPTIONS.get(sort, "due_date"))

    paginator = Paginator(tasks, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Preserve the current filters/search/sort when building pagination links.
    querystring = request.GET.copy()
    querystring.pop("page", None)

    # Sort links add their own "sort" param, so they need it stripped out first.
    filters_querystring = querystring.copy()
    filters_querystring.pop("sort", None)

    context = {
        "page_obj": page_obj,
        "tasks": page_obj.object_list,
        "stats": stats,
        "categories": Category.objects.filter(owner=request.user),
        "search": search,
        "selected_status": status,
        "selected_priority": priority,
        "selected_category": category_id,
        "overdue_only": overdue_only,
        "sort": sort,
        "status_choices": Task.Status.choices,
        "priority_choices": Task.Priority.choices,
        "querystring": querystring.urlencode(),
        "filters_querystring": filters_querystring.urlencode(),
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    context = {"task": task}
    return render(request, "tasks/task_detail.html", context)


@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            messages.success(request, "Task created.")
            return redirect("task-list")
    else:
        form = TaskForm(user=request.user)

    context = {"form": form}
    return render(request, "tasks/task_create.html", context)


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
            return redirect("task-list")
    else:
        form = TaskForm(instance=task, user=request.user)

    context = {"form": form, "task": task}
    return render(request, "tasks/task_update.html", context)


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)

    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect("task-list")
    return render(request, "tasks/task_delete.html", {"task": task})


@login_required
@require_POST
def task_toggle_status(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    task.status = Task.Status.PENDING if task.status == Task.Status.COMPLETED else Task.Status.COMPLETED
    task.save()

    redirect_url = request.POST.get("next")
    # "next" comes from the client, so it must be validated before we redirect
    # to it — otherwise a crafted link could send a logged-in user off-site.
    if redirect_url and url_has_allowed_host_and_scheme(redirect_url, allowed_hosts={request.get_host()}):
        return redirect(redirect_url)
    return redirect("task-list")


@login_required
def category_list(request):
    categories = Category.objects.filter(owner=request.user).annotate(task_count=Count("tasks"))
    return render(request, "tasks/category_list.html", {"categories": categories})


@login_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.save(commit=False)
            category.owner = request.user
            category.save()
            messages.success(request, "Category created.")
            return redirect("category-list")
    else:
        form = CategoryForm(user=request.user)
    return render(request, "tasks/category_form.html", {"form": form, "heading": "New category"})


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("category-list")
    else:
        form = CategoryForm(instance=category, user=request.user)
    return render(request, "tasks/category_form.html", {"form": form, "heading": "Edit category", "category": category})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, owner=request.user)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted.")
        return redirect("category-list")
    return render(request, "tasks/category_delete.html", {"category": category})
