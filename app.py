import tkinter as tk
from tkinter import ttk, messagebox, font, simpledialog
import json
from datetime import datetime, date
import os

class ChecklistApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Finish Your Checklist")
        self.root.geometry("400x600")  # Set a taller and narrower default window size
        self.root.configure(bg="#ffffff")
        
        # Try to load custom font, fallback to system font if unavailable
        # self.root.option_add("*Font", "Segoe UI 10")
        
        # Data storage
        self.data_file = "checklists.json"
        self.checklists = self.load_data()
        
        # Color scheme
        self.colors = {
            'bg': '#ffffff',
            'secondary_bg': '#f8f9fa',
            'accent': '#007AFF',
            'text': '#2c3e50',
            'subtle_text': '#95a5a6',
            'border': '#e1e4e8'
        }
        
        # Styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure styles
        self.style.configure('Custom.TFrame', background=self.colors['bg'])
        self.style.configure('Secondary.TFrame', background=self.colors['secondary_bg'])
        self.style.configure('Custom.TLabel', 
                           background=self.colors['bg'], 
                           foreground=self.colors['text'],
                           font=('Segoe UI', 10))
        self.style.configure('Header.TLabel',
                           background=self.colors['bg'],
                           foreground=self.colors['text'],
                           font=('Segoe UI', 14, 'bold'))
        self.style.configure('Title.TLabel',
                           background=self.colors['bg'],
                           foreground=self.colors['accent'],
                           font=('Arial', 18, 'bold'))
        
        # Custom button style
        self.style.configure('Accent.TButton',
                           background=self.colors['accent'],
                           foreground='white',
                           padding=(10, 5),
                           borderwidth=2,
                           relief='raised',
                           font=('Segoe UI', 10))
        
        # Completed task button style
        self.style.configure('Completed.TButton',
                           background='green',
                           foreground='white',
                           padding=(10, 5),
                           borderwidth=2,
                           relief='raised',
                           font=('Segoe UI', 10))
        
        # Entry style
        self.style.configure('Custom.TEntry',
                           fieldbackground=self.colors['secondary_bg'],
                           borderwidth=0,
                           padding=10)
        
        # Main layout
        self.setup_gui()
        
    def setup_gui(self):
        # Main container with padding
        main_container = ttk.Frame(self.root, style='Custom.TFrame', padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # App title
        title = ttk.Label(main_container, text="Finish Your Checklist", style='Title.TLabel')
        title.config(font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 10))
        
        # Top panel - Checklist management
        top_panel = ttk.Frame(main_container, style='Secondary.TFrame', padding="10")
        top_panel.pack(side=tk.TOP, fill=tk.X, padx=(0, 5), pady=0)
        
        # Checklist dropdown
        ttk.Label(top_panel, text="Select Checklist", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.checklist_combobox = ttk.Combobox(top_panel, state='readonly', style='Custom.TEntry', width=30)
        self.checklist_combobox.pack(side=tk.LEFT, padx=(0, 5))
        self.checklist_combobox.bind('<<ComboboxSelected>>', self.on_select_checklist)
        
        # Add new checklist button
        add_checklist_btn = ttk.Button(top_panel, text="+", command=self.create_checklist, style='Accent.TButton')
        add_checklist_btn.pack(side=tk.LEFT, padx=(5, 0))
        add_checklist_btn.config(width=2)  # Set width to fit the icon
        
        # Edit checklist button
        edit_checklist_btn = ttk.Button(top_panel, text="✏️", command=self.edit_checklist, style='Accent.TButton')
        edit_checklist_btn.pack(side=tk.LEFT, padx=(5, 0))
        edit_checklist_btn.config(width=2)  # Set width to fit the icon
        
        # Delete checklist button
        delete_checklist_btn = ttk.Button(top_panel, text="🗑️", command=self.delete_checklist, style='Accent.TButton')
        delete_checklist_btn.pack(side=tk.LEFT, padx=(5, 0))
        delete_checklist_btn.config(width=2)  # Set width to fit the icon
        
        # Bottom panel - Task management
        bottom_panel = ttk.Frame(main_container, style='Custom.TFrame', padding="10")
        bottom_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Task input with enter key binding
        task_frame = ttk.Frame(bottom_panel, style='Custom.TFrame')
        task_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.task_entry = ttk.Entry(task_frame, style='Custom.TEntry', width=30)
        self.task_entry.insert(0, "Add a new task")  # Add placeholder text
        self.task_entry.bind("<FocusIn>", lambda event: self.task_entry.delete(0, tk.END))  # Clear on focus
        self.task_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.task_entry.bind('<Return>', lambda e: self.add_task())
        
        add_task_btn = ttk.Button(task_frame, text="+",
                                  command=self.add_task,
                                  style='Accent.TButton')
        add_task_btn.pack(side=tk.LEFT, padx=(5, 0))
        add_task_btn.config(width=2)  # Set width to fit the icon
        
        # Control buttons for tasks
        control_frame = ttk.Frame(bottom_panel, style='Custom.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        refresh_btn = ttk.Button(control_frame, text="🔄", command=self.refresh_checklist, style='Accent.TButton')
        refresh_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        complete_all_btn = ttk.Button(control_frame, text="✔️", command=self.complete_all_tasks, style='Accent.TButton')
        complete_all_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Tasks display
        self.tasks_frame = ttk.Frame(bottom_panel, style='Custom.TFrame')
        self.tasks_frame.pack(fill=tk.BOTH, expand=True)
        
        # Update display
        self.update_checklist_display()
        
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                today = date.today().isoformat()
                for checklist in data.values():
                    if checklist.get('daily_refresh', False) and checklist.get('last_refresh', '') != today:
                        for task in checklist['tasks']:
                            task['done'] = False
                        checklist['last_refresh'] = today
                return data
        return {}
    
    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.checklists, f, indent=4)
            
    def create_checklist(self):
        name = simpledialog.askstring("New Checklist", "Enter the name of the new checklist:")
        if not name:
            return
        if name in self.checklists:
            messagebox.showwarning("Warning", "A checklist with this name already exists")
            return
            
        self.checklists[name] = {
            'daily_refresh': False,
            'tasks': [],
            'last_refresh': date.today().isoformat()
        }
        
        self.save_data()
        self.update_checklist_display()
        
    def edit_checklist(self):
        selected_checklist = self.checklist_combobox.get()
        if not selected_checklist:
            messagebox.showwarning("Warning", "Please select a checklist to edit")
            return

        new_name = simpledialog.askstring("Edit Checklist", "Enter the new name for the checklist:", initialvalue=selected_checklist)
        if new_name and new_name != selected_checklist:
            if new_name in self.checklists:
                messagebox.showwarning("Warning", "A checklist with this name already exists")
                return
            self.checklists[new_name] = self.checklists.pop(selected_checklist)
            self.save_data()
            self.update_checklist_display()
        
    def delete_checklist(self):
        selected_checklist = self.checklist_combobox.get()
        if not selected_checklist:
            messagebox.showwarning("Warning", "Please select a checklist to delete")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{selected_checklist}'?"):
            del self.checklists[selected_checklist]
            self.save_data()
            self.update_checklist_display()
            self.clear_tasks_display()
        
    def update_checklist_display(self):
        # Update the combobox with the list of checklists
        self.checklist_combobox['values'] = sorted(self.checklists.keys())
        if self.checklist_combobox['values']:
            self.checklist_combobox.current(0)  # Select the first checklist by default
            self.display_tasks(self.checklist_combobox.get())  # Display tasks for the first checklist
        
    def on_select_checklist(self, event):
        selected_checklist = self.checklist_combobox.get()
        if selected_checklist:
            self.display_tasks(selected_checklist)
        
    def add_task(self):
        task_text = self.task_entry.get().strip()
        if not task_text:
            messagebox.showwarning("Warning", "Task cannot be empty")
            return

        selected_checklist = self.checklist_combobox.get()
        if not selected_checklist:
            messagebox.showwarning("Warning", "No checklist selected")
            return

        self.checklists[selected_checklist]['tasks'].append({'text': task_text, 'done': False})
        self.save_data()
        self.display_tasks(selected_checklist)
        self.task_entry.delete(0, tk.END)  # Clear the entry after adding the task
        
    def toggle_task(self, checklist_name, task_idx):
        self.checklists[checklist_name]['tasks'][task_idx]['done'] = not self.checklists[checklist_name]['tasks'][task_idx]['done']
        self.save_data()
        self.display_tasks(checklist_name)
        
    def display_tasks(self, checklist_name):
        # Clear existing tasks
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

        # Create scrollable frame
        canvas = tk.Canvas(self.tasks_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tasks_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Custom.TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Bind mouse wheel to canvas for scrolling
        canvas.bind("<Enter>", lambda e: canvas.focus_set())  # Ensure focus on hover
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        canvas.bind("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))  # For Linux
        canvas.bind("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))   # For Linux

        # Bind arrow keys for scrolling
        canvas.bind("<Down>", lambda event: canvas.yview_scroll(1, "units"))
        canvas.bind("<Up>", lambda event: canvas.yview_scroll(-1, "units"))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Display tasks
        for i, task in enumerate(self.checklists[checklist_name]['tasks']):
            frame = ttk.Frame(scrollable_frame, style='Custom.TFrame')
            frame.pack(fill=tk.X, pady=5)

            # Task button
            task_button = ttk.Button(frame, text=task['text'],
                                     command=lambda i=i: self.toggle_task(checklist_name, i),
                                     style='Accent.TButton')
            task_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Change button color based on task completion
            if task['done']:
                task_button.configure(style='Completed.TButton')
            else:
                task_button.configure(style='Accent.TButton')

            # Edit button
            edit_btn = ttk.Button(frame, text="✏️", command=lambda i=i: self.edit_task(checklist_name, i))
            edit_btn.pack(side=tk.LEFT, padx=5)
            edit_btn.config(width=2)  # Set width to fit the emoji

            # Delete button
            delete_btn = ttk.Button(frame, text="🗑️", command=lambda i=i: self.delete_task(checklist_name, i))
            delete_btn.pack(side=tk.LEFT, padx=5)
            delete_btn.config(width=2)  # Set width to fit the emoji
            
    def edit_task(self, checklist_name, task_idx):
        task = self.checklists[checklist_name]['tasks'][task_idx]
        new_text = simpledialog.askstring("Edit Task", "Edit the task:", initialvalue=task['text'])
        if new_text is not None:
            task['text'] = new_text
            self.save_data()
            self.display_tasks(checklist_name)
            
    def delete_task(self, checklist_name, task_idx):
        del self.checklists[checklist_name]['tasks'][task_idx]
        self.save_data()
        self.display_tasks(checklist_name)
        
    def clear_tasks_display(self):
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

    def refresh_checklist(self):
        selected_checklist = self.checklist_combobox.get()
        if not selected_checklist:
            messagebox.showwarning("Warning", "No checklist selected")
            return

        # Logic to refresh the checklist (e.g., reset task statuses)
        for task in self.checklists[selected_checklist]['tasks']:
            task['done'] = False  # Example: Reset all tasks to not done

        self.save_data()
        self.display_tasks(selected_checklist)

    def complete_all_tasks(self):
        selected_checklist = self.checklist_combobox.get()
        if not selected_checklist:
            messagebox.showwarning("Warning", "No checklist selected")
            return

        # Mark all tasks as complete
        for task in self.checklists[selected_checklist]['tasks']:
            task['done'] = True

        self.save_data()
        self.display_tasks(selected_checklist)

def main():
    root = tk.Tk()
    app = ChecklistApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()