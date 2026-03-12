# DevOps Miles Python App

A simple Flask web application with a SQLite backend. The app takes your name, stores it in the database, and returns a greeting.

## Features
- Input your name via web form
- Stores name in SQLite database
- Returns personalized greeting

## Files
- app.py: Main application
- requirements.txt: Python dependencies
- migrate.py: DB setup script

## Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run DB migration: `python migrate.py`
3. Start app: `python app.py`

---

> For deployment, use Ansible playbook to copy files and run setup on VM.
