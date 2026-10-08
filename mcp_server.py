"""
=============================================================================
UNIVERSAL GENERAL-PURPOSE FASTMCP SERVER
=============================================================================
Exposes general-purpose and candidate-specific MCP tools.
=============================================================================
"""

import os
import sys
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("UniversalFastMCPServer")


# ==========================================================
# GENERAL PURPOSE MCP TOOLS
# ==========================================================

@mcp.tool()
def greet_user(name: str = "User") -> str:
    """Generate a friendly greeting."""

    return f"Hello {name}! Welcome to the Universal FastMCP Server Platform."


@mcp.tool()
def calculate_math(operation: str, a: float, b: float) -> str:
    """
    Perform mathematical calculations.

    operation:
    add, subtract, multiply, divide, power
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
        return f"Error: Unsupported operation '{operation}'."

    return f"FastMCP Math Tool Result: {a} {op_str} {b} = {res}"


@mcp.tool()
def check_prime(number: int) -> str:
    """Check whether a number is prime."""

    if number < 2:
        return f"{number} is NOT a prime number."

    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return f"{number} is NOT a prime number (divisible by {i})."

    return f"{number} IS a prime number!"


@mcp.tool()
def search_web_topic(topic: str) -> str:
    """
    Search a small knowledge base for technical topics.
    """

    kb = {
        "machine learning":
            "Machine Learning (ML) is a branch of AI that enables systems "
            "to learn and improve from data automatically without explicit programming.",

        "model context protocol":
            "Model Context Protocol (MCP) is an open standard connecting "
            "AI models to context sources and executable tools.",

        "python":
            "Python is a high-level, interpreted programming language widely "
            "used in AI, data science, web development, and automation.",

        "qdrant":
            "Qdrant is a high-performance vector database designed for "
            "neural search, embeddings, and payload filtering."
    }

    top_lower = topic.lower().strip()

    for key, value in kb.items():

        if key in top_lower or top_lower in key:
            return f"Web Search Information for '{topic}': {value}"

    return (
        f"Web Search Result for '{topic}': "
        "Information relates to computer science, AI engineering, "
        "and software development."
    )


# ==========================================================
# WEATHER TOOL
# ==========================================================

@mcp.tool()
def check_weather(city: str) -> str:
    """
    Check weather information for a city.

    Note:
    This currently uses simulated weather data for testing.
    """

    weather_data = {
        "delhi": {
            "temperature": "34°C",
            "condition": "Sunny",
            "humidity": "55%",
            "wind": "12 km/h"
        },

        "mumbai": {
            "temperature": "31°C",
            "condition": "Humid & Cloudy",
            "humidity": "82%",
            "wind": "14 km/h"
        },

        "gurgaon": {
            "temperature": "33°C",
            "condition": "Sunny",
            "humidity": "58%",
            "wind": "11 km/h"
        },

        "gurugram": {
            "temperature": "33°C",
            "condition": "Sunny",
            "humidity": "58%",
            "wind": "11 km/h"
        },

        "noida": {
            "temperature": "34°C",
            "condition": "Sunny",
            "humidity": "56%",
            "wind": "10 km/h"
        }
    }

    city_key = city.lower().strip()

    if city_key in weather_data:

        data = weather_data[city_key]

        return (
            f"Weather Report for {city.title()}:\n"
            f"Temperature: {data['temperature']}\n"
            f"Condition: {data['condition']}\n"
            f"Humidity: {data['humidity']}\n"
            f"Wind Speed: {data['wind']}\n"
            f"[Simulated data]"
        )

    return (
        f"Weather Report for {city.title()}:\n"
        f"Temperature: 30°C\n"
        f"Condition: Partly Cloudy\n"
        f"Humidity: 60%\n"
        f"Wind Speed: 10 km/h\n"
        f"[Simulated data]"
    )


# ==========================================================
# DOMAIN / RESUME MCP TOOLS
# ==========================================================

@mcp.tool()
def search_resume(query: str, category: str = "all") -> str:
    """
    Search Anmol Saharawat's resume information.
    """

    doc_path = "anmol_resume.txt"

    if not os.path.exists(doc_path):
        return f"Error: Document '{doc_path}' not found."

    with open(doc_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    query_lower = query.lower()

    sections = [
        section.strip()
        for section in raw_text.split("\n\n")
        if section.strip()
    ]

    matching_sections = []

    for section in sections:

        section_lower = section.lower()

        if category != "all" and category not in section_lower:
            continue

        if any(
            term in section_lower
            for term in query_lower.split()
        ):
            matching_sections.append(section)

    if not matching_sections:
        matching_sections = sections[:2]

    return "\n\n---\n\n".join(matching_sections)


@mcp.tool()
def calculate_experience(start_year: int, end_year: int) -> str:
    """Calculate experience duration."""

    if end_year < start_year:
        return "Error: End year cannot be earlier than start year."

    years = end_year - start_year
    months = years * 12

    return (
        f"Candidate experience duration: "
        f"{years} years ({months} months) "
        f"from {start_year} to {end_year}."
    )


@mcp.tool()
def get_candidate_skills(category: str = "all") -> str:
    """Retrieve candidate technical skills."""

    skills_data = {

        "languages": [
            "Python",
            "JavaScript",
            "HTML5",
            "CSS3",
            "SQL"
        ],

        "frameworks": [
            "Flask",
            "scikit-learn",
            "joblib",
            "Google GenAI SDK",
            "FastMCP"
        ],

        "databases": [
            "Qdrant Vector DB",
            "SQLite",
            "Chroma DB"
        ],

        "concepts": [
            "REST APIs",
            "API Security",
            "Semantic Search",
            "RAG Pipeline",
            "LLM Guardrails",
            "MCP Protocol"
        ]
    }

    category_lower = category.lower()

    if category_lower in skills_data:

        return (
            f"Candidate Skills "
            f"({category_lower.capitalize()}): "
            f"{', '.join(skills_data[category_lower])}"
        )

    all_skills = []

    for key, values in skills_data.items():

        all_skills.append(
            f"{key.capitalize()}: {', '.join(values)}"
        )

    return "\n".join(all_skills)


@mcp.tool()
def evaluate_candidate_fit(
    role_title: str,
    required_skills: str
) -> str:
    """Evaluate candidate fit for a role."""

    candidate_skills = [
        "python",
        "flask",
        "qdrant",
        "scikit-learn",
        "rag",
        "mcp",
        "html",
        "css",
        "sql",
        "gemini"
    ]

    required_list = [
        skill.strip().lower()
        for skill in required_skills.split(",")
    ]

    matched = [
        skill
        for skill in required_list
        if any(candidate in skill for candidate in candidate_skills)
    ]

    match_score = (
        len(matched) / len(required_list) * 100
        if required_list
        else 100
    )

    if match_score >= 70:
        fit_status = "EXCELLENT FIT"

    elif match_score >= 40:
        fit_status = "PARTIAL FIT"

    else:
        fit_status = "POOR FIT"

    return (
        f"Evaluation Summary for Role '{role_title}':\n"
        f"- Match Score: {match_score:.1f}%\n"
        f"- Fit Assessment: {fit_status}\n"
        f"- Matched Skills: "
        f"{', '.join(matched) if matched else 'None'}\n"
        f"- Profile Highlights: Strong hands-on experience "
        f"in Python, RAG pipelines, Qdrant Vector DB, "
        f"LLM Guardrails, and FastMCP."
    )


# ==========================================================
# SERVER START
# ==========================================================

if __name__ == "__main__":

    port = 8000

    if len(sys.argv) > 1 and sys.argv[1] == "stdio":

        print(
            "[+] Starting Universal FastMCP Server "
            "in stdio mode..."
        )

        mcp.run(transport="stdio")

    else:

        print(
            f"[+] Starting Universal FastMCP Server over SSE "
            f"on http://127.0.0.1:{port}/sse..."
        )

        mcp.run(
            transport="sse",
            host="127.0.0.1",
            port=port
        )
