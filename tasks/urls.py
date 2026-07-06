from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task-list'),
    path('<int:pk>/', views.task_detail, name='task-detail'),
    path('create/', views.task_create, name='task-create'),
    path('<int:pk>/update/', views.task_update, name='task-update'),
    path('<int:pk>/delete/', views.task_delete, name='task-delete'),
]