from django.shortcuts import render, get_object_or_404, redirect
from .models import Task
from .forms import TaskForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required
def task_list(request):
    all_tasks = Task.objects.filter(owner=request.user)
    context = {"tasks": all_tasks}
    return render(request, "tasks/task_list.html", context)

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    context = {"task": task}
    return render(request, "tasks/task_detail.html", context)

@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            return redirect("task-list")
    else:
        form = TaskForm()

    context = {
        'form': form
        } 
    return render(request, "tasks/task_create.html", context)

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("task-list")
    else:
        form = TaskForm(instance=task)
        
    context = {
        'form': form,
        "task": task
        } 
    return render(request, "tasks/task_update.html", context)

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect('task-list')
    return render(request, 'tasks/task_delete.html', {'task': task})
