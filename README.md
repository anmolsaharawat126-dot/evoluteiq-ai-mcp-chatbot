# 🤖 EvoluteIQ AI MCP Chatbot

An intelligent AI chatbot built using **Google Gemini, FastMCP, MCP-based tool execution, RAG, and Qdrant Vector Database**.

The system dynamically routes user queries to specialized tools, executes the appropriate MCP tool, sends the tool result to the LLM, and generates a grounded final response.

## 🚀 Live Demo

**Frontend:**
https://evoluteiq-ai-mcp-chatbot.vercel.app

**Backend API:**
https://evoluteiq-ai-mcp-chatbot.onrender.com

> Replace the frontend URL above with the exact Vercel deployment URL if it differs.

---

## ✨ Key Features

* 🧠 **Google Gemini-powered AI responses**
* 🔌 **FastMCP tool integration**
* 🔀 **Dynamic tool routing**
* 📚 **Resume-based RAG search**
* 🗄️ **Qdrant Vector Database integration**
* 🔐 **Tool approval workflow**
* 📊 **Detailed MCP execution tracing**
* 🌐 **Flask backend API**
* ⚡ **Vercel frontend deployment**
* ☁️ **Render backend deployment**
* 🛡️ **Grounded responses using tool outputs**
* 🧩 Specialized tools for different user queries

---

## 🏗️ Architecture

```text
                         ┌────────────────────┐
                         │       User         │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │  Vercel Frontend   │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │   Flask Backend    │
                         │      (Render)      │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │    MCP Agent       │
                         │  Query Router      │
                         └─────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
       │ FastMCP     │      │ Qdrant      │      │ Gemini      │
       │ Tools       │      │ Vector DB   │      │ LLM         │
       └─────────────┘      └─────────────┘      └─────────────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │  Grounded Final    │
                         │     Response       │
                         └────────────────────┘
```

---

## 🔧 MCP Tools

The chatbot currently supports multiple specialized tools:

| Tool                     | Purpose                                 |
| ------------------------ | --------------------------------------- |
| `calculate_math`         | Performs mathematical calculations      |
| `check_prime`            | Checks whether a number is prime        |
| `check_weather`          | Retrieves simulated weather information |
| `get_candidate_skills`   | Retrieves technical skills              |
| `search_resume`          | Searches candidate/resume information   |
| `calculate_experience`   | Calculates professional experience      |
| `evaluate_candidate_fit` | Evaluates candidate-role compatibility  |
| `search_web_topic`       | Handles topic-based searches            |
| `greet_user`             | Handles greeting requests               |

---

## 🔀 Intelligent Tool Routing

The agent analyzes the user's query and routes it to the most relevant tool.

### Example

**User:**

```text
What are Anmol's technical skills?
```

**MCP Agent:**

```text
get_candidate_skills
```

**Tool Result:**

```text
Languages: Python, JavaScript, HTML5, CSS3, SQL
Frameworks: Flask, scikit-learn, joblib, Google GenAI SDK, FastMCP
Databases: Qdrant Vector DB, SQLite, Chroma DB
Concepts: REST APIs, API Security, Semantic Search, RAG Pipeline,
LLM Guardrails, MCP Protocol
```

The result is then passed to Gemini to generate the final grounded response.

---

## 🔐 Tool Approval Workflow

Sensitive tools can be configured with an approval requirement.

Example:

```text
User Request
     │
     ▼
Tool Detection
     │
     ▼
Approval Required
     │
     ▼
User Approval
     │
     ▼
Tool Execution
     │
     ▼
Tool Result
     │
     ▼
Gemini
     │
     ▼
Final Response
```

The interface also displays the execution trace so users can see which tool was selected and what result was returned.

---

## 📊 MCP Execution Trace

The system provides transparent execution logs such as:

```text
1. User Input
2. Tool Called
3. Tool Arguments
4. Policy
5. Approval Request
6. User Decision
7. Tool Result
8. Result Sent to LLM
9. Final LLM Response
```

This makes the agent's tool execution process easier to debug and understand.

---

## 🧠 RAG Pipeline

The chatbot also supports resume-based retrieval using a vector database.

```text
User Query
    │
    ▼
Resume Search
    │
    ▼
Qdrant Vector Database
    │
    ▼
Relevant Information
    │
    ▼
Gemini
    │
    ▼
Grounded Response
```

This allows the chatbot to answer questions about the candidate using stored resume information instead of relying only on the LLM's general knowledge.

---

## 🛠️ Technology Stack

### Backend

* Python
* Flask
* FastMCP
* Google GenAI SDK
* Gunicorn

### AI / ML

* Google Gemini
* scikit-learn
* RAG
* Semantic Search
* LLM-based response synthesis

### Database

* Qdrant Vector Database
* SQLite
* Chroma DB

### Frontend

* HTML5
* CSS3
* JavaScript

### Deployment

* **Frontend:** Vercel
* **Backend:** Render
* **Source Control:** GitHub

---

## 📁 Project Structure

```text
evoluteiq-ai-mcp-chatbot/
│
├── app.py
├── mcp_agent.py
├── mcp_server.py
├── requirements.txt
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
└── README.md
```

---

## ⚙️ Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/anmolsaharawat126-dot/evoluteiq-ai-mcp-chatbot.git

cd evoluteiq-ai-mcp-chatbot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Environment

**Windows:**

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file or configure environment variables:

```text
GEMINI_API_KEY=your_gemini_api_key
QDRANT_API_KEY=your_qdrant_api_key
```

Never commit API keys or other secrets to GitHub.

### 6. Run Application

```bash
python app.py
```

The application will be available locally through the Flask server.

---

## 🧪 Tested Queries

The MCP routing system has been tested with:

### Technical Skills

```text
What are Anmol's technical skills?
```

→ `get_candidate_skills`

### Internship

```text
Tell me about Anmol's AI/ML internship experience.
```

→ `search_resume`

### Mathematics

```text
What is 25 multiplied by 4?
```

→ `calculate_math`

### Weather

```text
What is the weather in Mumbai?
```

→ `check_weather`

### Prime Number

```text
Is 29 a prime number?
```

→ `check_prime`

The tests confirm that queries are routed to the appropriate specialized tools without unnecessary tool execution.

---

## 🎯 Learning Outcomes

This project provided practical experience with:

* Model Context Protocol (MCP)
* FastMCP tool development
* AI agent architecture
* Dynamic tool routing
* LLM and tool interaction
* RAG pipelines
* Vector databases
* Gemini API integration
* Tool execution tracing
* Tool approval workflows
* API development with Flask
* Cloud deployment
* Debugging distributed frontend/backend applications

---

## 👨‍💻 Author

**Anmol Saharawat**

B.Tech Computer Science & Engineering

GitHub:
https://github.com/anmolsaharawat126-dot

LinkedIn:
https://linkedin.com/in/anmol-saharawat-75bb66322/

---

## 📌 Project Status

**Status: Completed and Deployed 🚀**

Frontend and backend are deployed separately, with the backend providing the AI/MCP agent and tool execution layer.
