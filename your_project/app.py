from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
    UserMixin,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///checklist_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ----- Models -----
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    
    tasks = db.relationship('Task', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    call_type = db.Column(db.String(50), nullable=False)
    checklist_type = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(250), nullable=False)
    done = db.Column(db.Boolean, default=False)
    parent_task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    # Relationship for subtasks (if any)
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]), lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ----- Default Tasks Data -----
DEFAULT_VOICEMAIL = [
    {'text': 'Purpose', 'done': False},
    {'text': 'Call to Action', 'done': False},
    {'text': 'Timeframe', 'done': False}
]

DEFAULT_SALES_START = [
    {'text': 'Rapport Question', 'done': False},
    {'text': '2nd Open Question', 'done': False},
    {'text': 'Value Add Item', 'done': False},
    {'text': 'Great Ask for Sale', 'done': False},
    {'text': 'Objection', 'done': False},
    {'text': 'Implement Sale Now or "How & When"', 'done': False},
    {'text': 'Anything Else they want to Ask?', 'done': False},
    {'text': 'Summarise Call', 'done': False},
    {'text': 'Book Followup or Next Steps', 'done': False}
]

DEFAULT_INTRODUCTION_START = [
    {'text': 'Repport Question', 'done': False},
    {'text': '2nd Open Question', 'done': False},
    {'text': 'Value Add Item', 'done': False},
    {'text': 'Learn their Current Situation', 'done': False},
    {'text': 'Learn their Desired Situation', 'done': False},
    {'text': 'Identify their Gap (& Problem Solve or Connect to Us)', 'done': False},
    {'text': 'Additional Support Required?', 'done': False},
    {'text': 'Anything Else they want to Ask?', 'done': False},
    {'text': 'Summarise Call', 'done': False},
    {'text': 'Book Next Call or Followup Steps', 'done': False}
]

DEFAULT_FOLLOWUP_START = [
    {'text': 'Rapport Question', 'done': False},
    {'text': '2nd Open Question', 'done': False},
    {'text': 'Value Add Item', 'done': False},
    {'text': 'Extra Support Required?', 'done': False},
    {'text': 'Anything they want to Ask?', 'done': False},
    {'text': 'Summarise Call', 'done': False},
    {'text': 'Book Followup or Next Steps', 'done': False}
]

DEFAULT_AT_RISK_START = [
    {'text': 'Rapport Question', 'done': False},
    {'text': '2nd Open Question', 'done': False},
    {'text': 'Uncover the Problem', 'done': False},
    {'text': 'Problem Solve', 'done': False},
    {'text': 'Objection', 'done': False},
    {'text': 'Connect course to Motivation/Their Gap', 'done': False},
    {'text': 'Great Ask for Sale', 'done': False},
    {'text': 'Additional Support Required', 'done': False},
    {'text': 'Summarise Call', 'done': False},
    {'text': 'Book Followup or Next Steps', 'done': False}
]

DEFAULT_SUPPORT_START = [
    {'text': 'Rapport Question', 'done': False},
    {'text': '2nd Open Question', 'done': False},
    {'text': 'Followup on Support Given Previously', 'done': False},
    {'text': 'Value Add Item', 'done': False},
    {'text': 'Objection', 'done': False},
    {'text': 'Further Support Required?', 'done': False},
    {'text': 'Anything Else they want to Ask?', 'done': False},
    {'text': 'Summarise Call', 'done': False},
    {'text': 'Book Followup or Next Steps', 'done': False}
]

DEFAULT_TASKS = {
    ("sales", "voicemail"): DEFAULT_VOICEMAIL,
    ("sales", "start call"): DEFAULT_SALES_START,
    ("reengagement", "voicemail"): DEFAULT_VOICEMAIL,
    ("reengagement", "start call"): DEFAULT_SALES_START,
    ("followup", "voicemail"): DEFAULT_VOICEMAIL,
    ("followup", "start call"): DEFAULT_FOLLOWUP_START,
    ("at-risk", "voicemail"): DEFAULT_VOICEMAIL,
    ("at-risk", "start call"): DEFAULT_AT_RISK_START,
    ("support", "voicemail"): DEFAULT_VOICEMAIL,
    ("support", "start call"): DEFAULT_SUPPORT_START,
    ("introduction", "voicemail"): DEFAULT_VOICEMAIL,
    ("introduction", "start call"): DEFAULT_INTRODUCTION_START,
}

DEFAULT_OBJECTION_SUBTASKS = [
    {'text': 'Listen & Acknowledge', 'done': False},
    {'text': 'Clarify & Question', 'done': False},
    {'text': 'Address the Objection', 'done': False},
    {'text': 'Confirm & Close', 'done': False}
]


# ----- Helper to Prepopulate Tasks -----
def populate_default_tasks(user, call_type, checklist_type):
    # Only populate if the user has no tasks (ignoring subtasks) for this combo
    existing = Task.query.filter_by(
        user_id=user.id, call_type=call_type, checklist_type=checklist_type, parent_task_id=None
    ).first()
    if existing is None:
        defaults = DEFAULT_TASKS.get((call_type, checklist_type), [])
        for task_def in defaults:
            new_task = Task(
                user_id=user.id,
                call_type=call_type,
                checklist_type=checklist_type,
                text=task_def['text'],
                done=task_def['done']
            )
            db.session.add(new_task)
        db.session.commit()

    # For Sales/Support Start Call, add the objection task and its sub‑checklist
    if checklist_type.lower() == "start call" and call_type.lower() in ["sales", "support"]:
        # Create the main objection task
        objection_task = Task(
            user_id=user.id,
            call_type=call_type,
            checklist_type=checklist_type,
            text="Objection",
            done=False
        )
        db.session.add(objection_task)
        db.session.flush()  # flush so we get objection_task.id for the subtasks
        
        # Create the objection sub‑checklist using the items from example.py
        objection_subtasks = [
            Task(user_id=user.id, call_type=call_type, checklist_type=checklist_type, 
                 text="Listen & Acknowledge", done=False, parent_task_id=objection_task.id),
            Task(user_id=user.id, call_type=call_type, checklist_type=checklist_type, 
                 text="Clarify & Question", done=False, parent_task_id=objection_task.id),
            Task(user_id=user.id, call_type=call_type, checklist_type=checklist_type, 
                 text="Address the Objection", done=False, parent_task_id=objection_task.id),
            Task(user_id=user.id, call_type=call_type, checklist_type=checklist_type, 
                 text="Confirm & Close", done=False, parent_task_id=objection_task.id)
        ]
        db.session.add_all(objection_subtasks)
        db.session.commit()


# ----- Routes -----
@app.route("/")
@login_required
def home():
    call_types = ["sales", "reengagement", "followup", "at-risk", "support", "introduction"]
    return render_template("home.html", call_types=call_types)


@app.route("/call/<call_type>")
@login_required
def call_sub_menu(call_type):
    checklist_options = ["voicemail", "start call"]
    return render_template("call_sub_menu.html", call_type=call_type, checklist_options=checklist_options)


@app.route("/checklist/<call_type>/<checklist_type>")
@login_required
def checklist(call_type, checklist_type):
    populate_default_tasks(current_user, call_type, checklist_type)
    tasks = Task.query.filter_by(
        user_id=current_user.id,
        call_type=call_type,
        checklist_type=checklist_type,
        parent_task_id=None
    ).order_by(Task.id).all()
    return render_template("checklist.html", call_type=call_type, checklist_type=checklist_type, tasks=tasks)


@app.route("/toggle_task/<int:task_id>")
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner.id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("home"))
    # For Objection tasks in Sales or Support (Start Call), initialize sub-checklist if needed.
    if task.text == "Objection" and task.call_type in ["sales", "support"] and task.checklist_type == "start call":
        if not task.subtasks:
            for sub in DEFAULT_OBJECTION_SUBTASKS:
                subtask = Task(
                    user_id=current_user.id,
                    call_type=task.call_type,
                    checklist_type=task.checklist_type,
                    text=sub['text'],
                    done=sub['done'],
                    parent_task_id=task.id
                )
                db.session.add(subtask)
            db.session.commit()
            flash("Objection sub-checklist initialized", "info")
            return redirect(url_for("checklist", call_type=task.call_type, checklist_type=task.checklist_type))
    else:
        task.done = not task.done
        db.session.commit()
    return redirect(url_for("checklist", call_type=task.call_type, checklist_type=task.checklist_type))


@app.route("/toggle_subtask/<int:subtask_id>")
@login_required
def toggle_subtask(subtask_id):
    subtask = Task.query.get_or_404(subtask_id)
    if subtask.owner.id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("home"))
    subtask.done = not subtask.done
    db.session.commit()
    parent_task = Task.query.get(subtask.parent_task_id)
    return redirect(url_for("checklist", call_type=parent_task.call_type, checklist_type=parent_task.checklist_type))


@app.route("/add_task/<call_type>/<checklist_type>", methods=["POST"])
@login_required
def add_task(call_type, checklist_type):
    text = request.form.get("task_text", "").strip()
    if not text:
        flash("Task cannot be empty", "warning")
    else:
        new_task = Task(
            user_id=current_user.id,
            call_type=call_type,
            checklist_type=checklist_type,
            text=text,
            done=False
        )
        db.session.add(new_task)
        db.session.commit()
        flash("Task added", "success")
    return redirect(url_for("checklist", call_type=call_type, checklist_type=checklist_type))


@app.route("/delete_task/<int:task_id>")
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner.id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("home"))
    if task.subtasks:
        for sub in task.subtasks:
            db.session.delete(sub)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted", "info")
    return redirect(url_for("checklist", call_type=task.call_type, checklist_type=task.checklist_type))


@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner.id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("home"))
    if request.method == "POST":
        new_text = request.form.get("task_text", "").strip()
        if new_text:
            task.text = new_text
            db.session.commit()
            flash("Task updated", "success")
            return redirect(url_for("checklist", call_type=task.call_type, checklist_type=task.checklist_type))
        else:
            flash("Task cannot be empty", "warning")
    return render_template("edit_task.html", task=task)


@app.route('/new_call/<call_type>/<checklist_type>', methods=['GET'])
@login_required
def new_call(call_type, checklist_type):
    # Delete all tasks for the current user with the provided call type and checklist type.
    tasks = Task.query.filter_by(user_id=current_user.id, call_type=call_type, checklist_type=checklist_type).all()
    for task in tasks:
        db.session.delete(task)
    db.session.commit()

    # Re-populate the default tasks (which includes the Objection task and its sub‑checklist if applicable)
    populate_default_tasks(current_user, call_type, checklist_type)
    
    flash("Checklist has been refreshed for a new call.", "success")
    return redirect(url_for('checklist', call_type=call_type, checklist_type=checklist_type))


# ----- Authentication Routes -----
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Username and password required", "warning")
            return redirect(url_for("register"))
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already taken", "warning")
            return redirect(url_for("register"))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)