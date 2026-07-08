# Task Manager

This app is a simple task manager that allows you to (create - view - edit - delete) your tasks,
and it has an authentication system that assigns each user his own tasks.

## Features
- User registration, login, logout
- Create, view, edit, delete tasks
- Each user only sees their own tasks

## Requirements
- Python 3.12.10
- Django 5.2.15

## Setup
1. Clone the repo and enter the project folder => `git clone <repo url>` && `cd task_manager` 
2. Create and activate a virtual environment => `python -m venv venv` && `source venv/Scripts/activate`
3. install project requirements => `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in real values (SECRET_KEY, DATABASE_URL, etc.)
5. `python manage.py migrate`
6. (optional) `python manage.py createsuperuser`
7. `python manage.py runserver`

## Running tests
`python manage.py test`

## Project structure
- `tasks/` — task CRUD
- `accounts/` — auth & registration
- `config/` — settings, root URLs