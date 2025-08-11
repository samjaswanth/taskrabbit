from flask import Flask, render_template_string, request, redirect, url_for
from jira_creator import app, JiraState
from openai import OpenAI
import httpx
import base64
import subprocess
import json
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx.Client(verify=False))

app_ui = Flask(__name__)

WELCOME_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <title>AI Assistant Entry</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-5">
    <div class="card shadow p-4">
        <h2 class="text-center">How can i help you?</h2>
        <form method="post">
            <div class="mb-3">
                <textarea name="user_prompt" class="form-control" rows="4" placeholder="Describe what you want..." required></textarea>
            </div>
            <button type="submit" class="btn btn-success w-100">Ask</button>
        </form>
    </div>
</div>
</body>
</html>
"""

@app_ui.route("/", methods=["GET", "POST"])
def welcome():
    if request.method == "POST":
        prompt = request.form["user_prompt"]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a routing assistant. Based on the user input, route to 'jira', 'kyc', or 'git'. Reply only with one word: 'jira', 'kyc', or 'git'."},
                {"role": "user", "content": prompt}
            ]
        )
        route_decision = response.choices[0].message.content.strip().lower()

        if route_decision == "jira":
            return redirect(url_for("jira_page"))
        elif route_decision == "kyc":
            return redirect(url_for("kyc_page"))
        elif route_decision == "git":
            return redirect(url_for("git_page"))
        else:
            return "<h4 style='text-align:center;margin-top:20px;'>I can help with tasks like Jira ticketing, KYC processing, and Git operations.</h4>"

    return render_template_string(WELCOME_TEMPLATE)

GIT_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <title>Git Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-5">
    <div class="card shadow p-4">
        <h2 class="text-center">🛠️ Git Automation Assistant</h2>
        <form method="post">
            <div class="mb-3">
                <textarea name="git_prompt" class="form-control" rows="4" placeholder="e.g., create branch feature/login" required></textarea>
            </div>
            {% if command %}
            <div class="mb-3">
                <label class="form-label">Generated Command:</label>
                <pre class="p-2 bg-light border rounded">{{ command }}</pre>
                <button name="confirm" value="yes" class="btn btn-success">Confirm and Run</button>
                <button name="confirm" value="no" class="btn btn-danger">Cancel</button>
            </div>
            {% else %}
            <button type="submit" class="btn btn-dark w-100">Generate Git Command</button>
            {% endif %}
        </form>

        {% if output %}
        <div class="mt-4">
            <h5>Command Output</h5>
            <pre class="p-3 bg-light border rounded">{{ output }}</pre>
        </div>
        {% endif %}
    </div>
</div>
</body>
</html>
"""

@app_ui.route("/git", methods=["GET", "POST"])
def git_page():
    output = None
    command = None

    if request.method == "POST":
        prompt = request.form.get("git_prompt")
        confirmation = request.form.get("confirm")

        if prompt and not confirmation:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a DevOps assistant. Convert the user's intent into a Git command. Return only the valid git CLI command."},
                    {"role": "user", "content": prompt}
                ]
            )
            command = response.choices[0].message.content.strip()
            return render_template_string(GIT_TEMPLATE, output=None, command=command)

        elif confirmation == "yes":
            command = request.form.get("command")
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                output = result.stdout + result.stderr
            except Exception as e:
                output = f"Error running command: {e}"
            return render_template_string(GIT_TEMPLATE, output=output, command=None)

        elif confirmation == "no":
            return render_template_string(GIT_TEMPLATE, output="Command cancelled by user.", command=None)

    return render_template_string(GIT_TEMPLATE, output=None, command=None)


JIRA_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <title>AI-Powered Jira Ticket Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            padding-top: 40px;
        }
        .container {
            max-width: 700px;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        h2 {
            font-weight: 600;
            margin-bottom: 30px;
            text-align: center;
        }
        .result-box {
            margin-top: 30px;
            background-color: #eef2f7;
            padding: 20px;
            border-radius: 10px;
        }
        .result-box p {
            margin: 5px 0;
        }
        .btn-submit {
            width: 100%;
        }
    </style>
</head>
<body>
<div class="container">
    <h2>Intelligent Jira Assistant</h2>
    <form method="post">
        <div class="mb-3">
            <label class="form-label">Summary</label>
            <input type="text" class="form-control" name="summary" placeholder="Enter issue summary..." required>
        </div>
        <div class="mb-3">
            <label class="form-label">Description</label>
            <textarea class="form-control" name="description" rows="6" placeholder="Enter detailed description..." required></textarea>
        </div>
        <button type="submit" class="btn btn-primary btn-submit">Submit</button>
    </form>

    {% if result %}
        <div class="result-box mt-4">
            <h5>🗘️ Result</h5>
            <p><strong>Severity:</strong> {{ result['severity'] }}</p>
            <p><strong>Status:</strong> {{ result['status'] }}</p>
            {% if result['issue_key'] %}
                <p><strong>Jira Ticket:</strong> 
                    <a href="https://altimetrik-team-demo.atlassian.net/browse/{{ result['issue_key'] }}" 
                       target="_blank">{{ result['issue_key'] }}</a>
                </p>
            {% endif %}
        </div>
    {% endif %}
</div>
</body>
</html>
"""

@app_ui.route("/jira", methods=["GET", "POST"])
def jira_page():
    result = None
    if request.method == "POST":
        summary = request.form["summary"]
        description = request.form["description"]

        initial = JiraState(summary=summary, description=description)
        output = app.invoke(initial)

        result = {
            "severity": output.get("severity", "Unknown"),
            "status": output.get("status", "Failure"),
            "issue_key": output.get("issue_key", "")
        }

    return render_template_string(JIRA_TEMPLATE, result=result)

KYC_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <title>KYC Document Upload</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-5">
    <div class="card shadow p-4">
        <h2 class="text-center">Upload KYC Document</h2>
        <form method="post" enctype="multipart/form-data">
            <div class="mb-3">
                <input type="file" name="kyc_image" accept="image/*" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Extract</button>
        </form>

        {% if extracted %}
        <div class="mt-4">
            <h5>Extracted ({{ doc_type.title() }})</h5>
            <pre class="p-3 bg-light border rounded">{{ extracted }}</pre>
        </div>
        {% endif %}
    </div>
</div>
</body>
</html>
"""

@app_ui.route("/kyc", methods=["GET", "POST"])
def kyc_page():
    extracted = None
    doc_type = ""
    if request.method == "POST":
        uploaded_file = request.files.get("kyc_image")
        if uploaded_file:
            image_bytes = uploaded_file.read()
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            mime_type = "image/jpeg"
            base64_url = f"data:{mime_type};base64,{encoded}"

            classify_prompt = "Classify the document. Give only one word like 'aadhaar', 'pan', 'default'."
            doc_type = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": classify_prompt},
                        {"type": "image_url", "image_url": {"url": base64_url}}
                    ]}
                ]
            ).choices[0].message.content.strip().lower()

            with open("docClassify.json", "r") as f:
                prompt_bank = json.load(f)

            selected_prompt = prompt_bank.get(doc_type, prompt_bank.get("default", "Extract relevant fields."))

            extracted = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": selected_prompt},
                        {"type": "image_url", "image_url": {"url": base64_url}}
                    ]}
                ]
            ).choices[0].message.content.strip()

    return render_template_string(KYC_TEMPLATE, extracted=extracted, doc_type=doc_type)

if __name__ == "__main__":
    app_ui.run(debug=True, port=5000)
