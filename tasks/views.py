from django.shortcuts import render, get_object_or_404, redirect
from .models import Task
from .forms import TaskForm
from django.contrib import messages
# Create your views here.

def task_list(request):
    all_tasks = Task.objects.all()
    context = {"tasks": all_tasks}
    return render(request, "tasks/task_list.html", context)

def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    context = {"task": task}
    return render(request, "tasks/task_detail.html", context)

def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("task_list")
    else:
        form = TaskForm()

    context = {
        'form': form
        } 
    return render(request, "tasks/task_create.html", context)

def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("task_list")
    else:
        form = TaskForm(instance=task)
        
    context = {
        'form': form,
        "task": task
        } 
    return render(request, "tasks/task_update.html", context)


def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect('task_list')
    return render(request, 'tasks/task_delete.html', {'task': task})
