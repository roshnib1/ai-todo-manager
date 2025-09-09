from flask import Flask, render_template, request, redirect, url_for
from huggingface_hub import InferenceApi

app = Flask(__name__)

tasks = []
ai_tasks = []

# Hugging Face Setup 
HF_TOKEN = "xxxxxxxxxxxxxxxxxx"  # Replace with your token
inference = InferenceApi(repo_id="gpt2", token=HF_TOKEN)


def generate_ai_tasks(interests=''):
    """Generate AI-based tasks using Hugging Face or fallback to static tasks."""
    if interests:
        prompt = f"Suggest 3 short learning or productivity tasks related to '{interests}':"
        try:
            response = inference(prompt)
            # Hugging Face may return a list or string
            if isinstance(response, list):
                tasks_list = [t.strip() for t in response if t.strip()]
            else:
                tasks_list = [t.strip() for t in response.split("\n") if t.strip()]
        except:
            tasks_list = [
                f"Learn Python Data Analysis related to {interests}",
                f"Read AI News Articles related to {interests}",
                f"Build a Flask App related to {interests}"
            ]
    else:
        tasks_list = [
            "Learn Python Data Analysis",
            "Read AI News Articles",
            "Build a Flask App"
        ]

    ai_task_dicts = [
        {"id": idx+1, "task": t, "ai_reason": f"Suggested based on '{interests}'"} 
        for idx, t in enumerate(tasks_list[:3])
    ]
    return ai_task_dicts

#Routes
@app.route('/')
def home():
    completed_count = len([t for t in tasks if t.get('status') == 'Completed'])
    pending_count = len(tasks) - completed_count
    edit_id = request.args.get('edit_id', type=int)
    return render_template(
        'index.html',
        tasks=tasks,
        ai_tasks=ai_tasks,
        completed_count=completed_count,
        pending_count=pending_count,
        ai_count=len(ai_tasks),
        edit_id=edit_id
    )

@app.route('/add', methods=['POST'])
def add_task():
    task_name = request.form.get('task')
    tasks.append({'id': len(tasks)+1, 'task': task_name, 'progress': 0, 'notes': '', 'status': 'Pending'})
    return redirect(url_for('home'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    global tasks
    tasks = [t for t in tasks if t['id'] != task_id]
    return redirect(url_for('home'))

@app.route('/generate', methods=['GET'])
def generate():
    interests = request.args.get('interests', '')
    global ai_tasks
    ai_tasks = generate_ai_tasks(interests)
    return redirect(url_for('home'))

@app.route('/add_ai_task', methods=['POST'])
def add_ai_task():
    global ai_tasks
    task_id = request.form.get('task_id')
    if ai_tasks:
        task = next((t for t in ai_tasks if str(t.get('id')) == str(task_id)), None)
        if task:
            ai_tasks.remove(task)
            task['id'] = len(tasks) + 1
            task['progress'] = 0
            task['status'] = 'Pending'
            tasks.append(task)
    return redirect(url_for('home'))

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    for task in tasks:
        if task['id'] == task_id:
            task['status'] = 'Completed'
            task['progress'] = 100
            break
    return redirect(url_for('home'))

@app.route('/update_progress/<int:task_id>', methods=['POST'])
def update_progress(task_id):
    progress = int(request.form.get('progress', 0))
    for task in tasks:
        if task['id'] == task_id:
            task['progress'] = max(0, min(100, progress))
            task['status'] = 'Completed' if task['progress'] == 100 else 'Pending'
            break
    return redirect(url_for('home'))

@app.route('/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    task = next((t for t in tasks if t['id'] == task_id), None)
    if task:
        task['task'] = request.form.get('task')
        task['notes'] = request.form.get('notes', '')
        task['progress'] = int(request.form.get('progress', task['progress']))
        task['status'] = 'Completed' if task['progress'] == 100 else 'Pending'
    return redirect(url_for('home'))

# Run #
if __name__ == '__main__':
    app.run(debug=True)
