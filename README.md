# 🤖 Invento Bot

Invento Bot is a **Rasa-powered conversational assistant** designed to handle inventory management interactions. It processes user queries, interacts with backend APIs (hosted in a separate Django repository), and provides natural language responses to streamline operational workflows.

---

## 🧩 Overview

This repository contains the **Rasa project** component of Invento Bot. It includes all configuration, training, and dialogue management files necessary to run and train the conversational AI model.

> ⚙️ The Django backend (for database operations and APIs) is maintained in a **separate repository**. This repo focuses solely on the conversational AI logic.

---

## 📁 Project Structure

```
Invento_Bot/
├── actions/                # Custom Python actions triggered by intents
├── data/                   # NLU and story training data
├── models/                 # Trained Rasa models (generated after training)
├── tests/                  # Rasa test cases for stories and NLU
├── config.yml              # Pipeline and policies configuration
├── credentials.yml         # Channel and API connection settings
├── domain.yml              # Intents, entities, slots, and responses
├── endpoints.yml           # Backend service endpoints (e.g., Django APIs)
├── README.md               # Project documentation (this file)
└── .gitignore              # Git exclusions
```

---

## ⚙️ Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # On Windows
# or
source venv/bin/activate  # On Linux/Mac
```

### 2. Install Dependencies

If `requirements.txt` is missing, install Rasa manually:

```bash
pip install rasa
```

You can later generate a dependency file:

```bash
pip freeze > requirements.txt
```

### 3. Train the Model

```bash
rasa train
```

This command creates a new model file under the `models/` directory.

### 4. Run the Bot

To start the assistant in shell mode:

```bash
rasa shell
```

Or, to run with action server:

```bash
rasa run actions & rasa shell
```

### 5. Connect with Django Backend

Update your `endpoints.yml` with the Django API endpoint:

```yaml
action_endpoint:
  url: "http://localhost:8000/api/actions/"
```

Make sure the backend server is running before testing integrated flows.

---

## 🧠 Key Files

| File               | Description                                          |
| ------------------ | ---------------------------------------------------- |
| `domain.yml`       | Defines intents, responses, entities, and actions    |
| `data/nlu.yml`     | Training examples for natural language understanding |
| `data/stories.yml` | Conversational stories for dialogue management       |
| `actions/`         | Contains Python code for custom business logic       |
| `endpoints.yml`    | Connects Rasa to Django backend APIs                 |

---

## 🧪 Testing

Run unit tests using:

```bash
rasa test
```

---

## 🧹 Cleaning Up Repository

Before pushing to GitHub, ensure the following files/folders are **not committed**:

```
venv/
rasa_env/
__pycache__/
models/
*.pyc
*.log
```

Add them to `.gitignore` if missing.

---
\
