"""
=============================================================================
UNIVERSAL GENERAL-PURPOSE FASTMCP SERVER
=============================================================================
Fulfills all directives from Mahesh Sir: Exposes both general-purpose tools 
(Greetings, Math, Prime Check, Web Search) and domain-specific tools 
(Vector RAG Search, Experience Calculator, Technical Skills, Candidate Fit).
=============================================================================
"""

import os
import sys
from fastmcp import FastMCP

# Initialize Universal FastMCP Server
mcp = FastMCP("UniversalFastMCPServer")

# ==========================================================
# 🛠️ GENERAL PURPOSE MCP TOOLS (ANY USE CASE)
# ==========================================================

@mcp.tool()
def greet_user(name: str = "User") -> str:
    """
    Generate a friendly, personalized greeting message for a user.
    
    Args:
        name: Name of the user to greet.
    """
    return f"Hello {name}! Welcome to the Universal FastMCP Server Platform."

@mcp.tool()
def calculate_math(operation: str, a: float, b: float) -> str:
    """
    Perform general mathematical arithmetic calculations.
    
    Args:
        operation: Calculation operation ('add', 'subtract', 'multiply', 'divide', 'power').
        a: First number.
        b: Second number.
    """
    op = operation.lower().strip()
    if op in ["add", "+", "addition"]:
        res = a + b
        op_str = "+"
    elif op in ["subtract", "-", "subtraction"]:
        res = a - b
        op_str = "-"
    elif op in ["multiply", "*", "multiplication"]:
        res = a * b
        op_str = "*"
    elif op in ["divide", "/", "division"]:
        if b == 0:
            return "Error: Division by zero is undefined."
        res = a / b
        op_str = "/"
    elif op in ["power", "^", "pow"]:
        res = a ** b
        op_str = "^"
    else:
        res = a + b
        op_str = "+"

    return f"FastMCP Math Tool Result: {a} {op_str} {b} = {res}"

@mcp.tool()
def check_prime(number: int) -> str:
    """
    Check if a given integer is a prime number.
    
    Args:
        number: Integer number to check.
    """
    if number < 2:
        return f"{number} is NOT a prime number."
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return f"{number} is NOT a prime number (divisible by {i})."
    return f"{number} IS a prime number!"

@mcp.tool()
def search_web_topic(topic: str) -> str:
    """
    Search web knowledge topic information (web search / scraping simulation).
    
    Args:
        topic: General topic string to research.
    """
    kb = {
        "machine learning": "Machine Learning (ML) is a branch of AI that enables systems to learn and improve from data automatically without explicit programming.",
        "model context protocol": "Model Context Protocol (MCP) is an open standard connecting AI models to context sources and executable tools via standardized JSON-RPC protocols.",
        "python": "Python is a high-level, interpreted programming language widely used in AI, data science, web development, and automation.",
        "qdrant": "Qdrant is a high-performance vector database engineered for neural search, embedding matching, and payload filtering."
    }
    top_lower = topic.lower().strip()
    for k, v in kb.items():
        if k in top_lower or top_lower in k:
            return f"Web Search Information for '{topic}': {v}"
    
    return f"Web Search Result for '{topic}': Information retrieved successfully. Concept relates to computer science, AI engineering, and software development."

# ==========================================================
# 🛠️ DOMAIN & RESUME SPECIFIC MCP TOOLS
# ==========================================================

@mcp.tool()
def search_resume(query: str, category: str = "all") -> str:
    """
    Search candidate Anmol Saharawat's resume database for projects, education, internship, or background.
    
    Args:
        query: Specific search query string.
        category: Optional category filter ('all', 'work_experience', 'skills', 'education', 'summary').
    """
    doc_path = "anmol_resume.txt"
    if not os.path.exists(doc_path):
        return f"Error: Document '{doc_path}' not found."

    with open(doc_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    query_lower = query.lower()
    sections = [s.strip() for s in raw_text.split("\n\n") if s.strip()]
    
    matching_sections = []
    for sec in sections:
        sec_lower = sec.lower()
        if category != "all" and category not in sec_lower:
            continue
        if any(term in sec_lower for term in query_lower.split()):
            matching_sections.append(sec)

    if not matching_sections:
        matching_sections = sections[:2]

    return "\n\n---\n\n".join(matching_sections)

@mcp.tool()
def calculate_experience(start_year: int, end_year: int) -> str:
    """
    Calculate work experience duration and total years between start and end years.
    
    Args:
        start_year: Starting year (e.g. 2024).
        end_year: Ending year or current year (e.g. 2026).
    """
    if end_year < start_year:
        return "Error: End year cannot be earlier than start year."
    
    years = end_year - start_year
    months = years * 12
    return f"Candidate experience duration: {years} years ({months} months) from {start_year} to {end_year}."

@mcp.tool()
def get_candidate_skills(category: str = "all") -> str:
    """
    Retrieve candidate technical skills across programming languages, frameworks, vector databases, and concepts.
    
    Args:
        category: Filter category ('languages', 'frameworks', 'databases', 'concepts', 'all').
    """
    skills_data = {
        "languages": ["Python", "JavaScript", "HTML5", "CSS3", "SQL"],
        "frameworks": ["Flask", "scikit-learn", "joblib", "Google GenAI SDK", "FastMCP"],
        "databases": ["Qdrant Vector DB", "SQLite", "Chroma DB"],
        "concepts": ["REST APIs", "API Security", "Semantic Search", "RAG Pipeline", "LLM Guardrails", "MCP Protocol"]
    }
    
    cat_lower = category.lower()
    if cat_lower in skills_data:
        return f"Candidate Skills ({cat_lower.capitalize()}): {', '.join(skills_data[cat_lower])}"
    
    all_skills_str = []
    for k, v in skills_data.items():
        all_skills_str.append(f"{k.capitalize()}: {', '.join(v)}")
    
    return "\n".join(all_skills_str)

@mcp.tool()
def evaluate_candidate_fit(role_title: str, required_skills: str) -> str:
    """
    Evaluate candidate Anmol Saharawat's match percentage and fit for a specific target job role.
    
    Args:
        role_title: Job title (e.g. 'AI/ML Developer Intern', 'Full Stack Engineer').
        required_skills: Comma-separated list of required technical skills.
    """
    candidate_skills = ["python", "flask", "qdrant", "scikit-learn", "rag", "mcp", "html", "css", "sql", "gemini"]
    req_list = [s.strip().lower() for s in required_skills.split(",")]
    
    matched = [s for s in req_list if any(cs in s for cs in candidate_skills)]
    match_score = (len(matched) / len(req_list)) * 100 if req_list else 100
    
    fit_status = "EXCELLENT FIT" if match_score >= 70 else "PARTIAL FIT" if match_score >= 40 else "POOR FIT"
    
    return (
        f"Evaluation Summary for Role '{role_title}':\n"
        f"- Match Score: {match_score:.1f}%\n"
        f"- Fit Assessment: {fit_status}\n"
        f"- Matched Skills: {', '.join(matched) if matched else 'None'}\n"
        f"- Profile Highlights: Strong hands-on experience in Python, RAG pipelines, Qdrant Vector DB, LLM Guardrails, and FastMCP."
    )

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        print("[+] Starting Universal FastMCP Server in stdio mode...")
        mcp.run(transport="stdio")
    else:
        print(f"[+] Starting Universal FastMCP Server over SSE / Streamable HTTP on http://127.0.0.1:{port}/sse...")
        mcp.run(transport="sse", host="127.0.0.1", port=port)
