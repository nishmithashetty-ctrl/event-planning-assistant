Event Planning Assistant

An AI-powered Event Planning Assistant built using **NVIDIA NAT** and a **ReAct agent architecture**.
The system intelligently plans, manages, and automates event workflows using dynamic tool orchestration.

---

## 🚀 Features

* 🧠 ReAct-based reasoning agent
* 📁 Local file system access
* ☁️ Google Drive integration (via MCP)
* 👥 Participant registration & management
* 🌦 Weather checking capability
* 📊 Workflow-based task execution
* 🔎 Optional RAG (Embedder + Retriever support)

---

## 🏗 Architecture

This project is built using:

* **NVIDIA NAT Framework**
* **ReAct Agent**
* **Tool-based modular design**
* **MCP (Model Context Protocol)**
* **Google OAuth2 authentication**
* **Vector store (for retrieval use cases)**

The agent dynamically selects tools based on user input and reasons step-by-step before executing actions.

---

## 📂 Project Structure

```
event-planning-project/
│
├── config_react.yml
├── config_react_with_gdrive.yml
├── mcp_tools.py
├── participant_manager.py
├── theme_generator.py
├── vector_store/
├── token.pickle (ignored)
├── .env (ignored)
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Create Virtual Environment

```bash
conda create -n nemo-env311 python=3.11
conda activate nemo-env311
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set Environment Variables

Create a `.env` file:

```
NVIDIA_API_KEY=your_api_key
```

⚠️ Do not upload `.env` or OAuth secrets to GitHub.

---

## ▶️ Run the Project

```bash
nat run --config_file config_react.yml --input "Generate 5 wedding themes"
```

With Google Drive support:

```bash
nat run --config_file config_react_with_gdrive.yml --input "Upload event summary to drive"
```

---

## 🧠 RAG Extension (Optional)

The system supports:

* Embedders
* Retrievers
* Vector store integration

This enables contextual memory and document-based question answering.

---

## 🔐 Security Notes

The following are excluded from version control:

* `token.pickle`
* `client_secret.json`
* `.env`
* Vector store files

---

## 📌 Use Case

This assistant helps automate event planning by:

* Generating themes
* Managing participants
* Checking weather
* Storing and retrieving event data
* Integrating with Google Drive
* Orchestrating tools intelligently

---


