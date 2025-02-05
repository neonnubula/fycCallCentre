#!/bin/bash
# This script creates the project directory structure for the Checklist Flask app.

# Define the main project directory name
PROJECT_DIR="your_project"

# Create the main project directory and the templates subdirectory
mkdir -p "$PROJECT_DIR/templates"

# Create the main files
touch "$PROJECT_DIR/app.py"
touch "$PROJECT_DIR/requirements.txt"
# (The database file 'checklist_app.db' will be created automatically by the app, so no need to create it manually.)

# Create the template files
touch "$PROJECT_DIR/templates/base.html"
touch "$PROJECT_DIR/templates/home.html"
touch "$PROJECT_DIR/templates/call_sub_menu.html"
touch "$PROJECT_DIR/templates/checklist.html"
touch "$PROJECT_DIR/templates/edit_task.html"
touch "$PROJECT_DIR/templates/login.html"
touch "$PROJECT_DIR/templates/register.html"

echo "Project structure created in '$PROJECT_DIR'." 