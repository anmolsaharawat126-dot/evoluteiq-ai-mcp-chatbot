"""
=============================================================================
SMART DYNAMIC MCP AI AGENT
Universal FastMCP Tool Runner
=============================================================================
"""

import os
import re

from google import genai

from mcp_server import (
    greet_user,
    calculate_math,
    check_prime,
    search_web_topic,
    check_weather,
    search_resume,
    calculate_experience,
    get_candidate_skills,
    evaluate_candidate_fit
)


# ==========================================================
# GEMINI KEY
# ==========================================================

def get_gemini_key():

    key = os.environ.get("GEMINI_API_KEY", "")

    if key:
        return key

    try:

        if os.path.exists("app.py"):

            with open(
                "app.py",
                "r",
                encoding="utf-8"
            ) as f:

                for line in f:

                    if (
                        "GEMINI_API_KEY =" in line
                        and
                        "PASTE_YOUR_REAL_GEMINI_API_KEY_HERE"
                        not in line
                    ):

                        extracted_key = (
                            line
                            .split("=")[1]
                            .strip()
                            .strip('"')
                            .strip("'")
                        )

                        if extracted_key:
                            return extracted_key

    except Exception as e:

        print(f"[-] Warning: {e}")

    return ""


# ==========================================================
# MAIN MCP QUERY RUNNER
# ==========================================================

def run_mcp_query(user_query: str) -> dict:

    """
    Dynamically routes user prompts to FastMCP tools.
    """

    tools_discovered = [
        "greet_user",
        "calculate_math",
        "check_prime",
        "search_web_topic",
        "check_weather",
        "search_resume",
        "calculate_experience",
        "get_candidate_skills",
        "evaluate_candidate_fit",
        "delete_file"
    ]

    query_lower = user_query.lower()

    tool_outputs = []
    tool_calls_detail = []

    math_matched = False

    # ======================================================
    # MATH
    # ======================================================

    MATH_STEMS = [
        "add",
        "plus",
        "sum",
        "multipli",
        "times",
        "divid",
        "subtract",
        "minus",
        "calculate",
        "math",
        "product",
        "power"
    ]

    numbers = [
        float(number)
        for number in re.findall(
            r"\d+(?:\.\d+)?",
            user_query
        )
    ]

    is_math = (
        any(
            stem in query_lower
            for stem in MATH_STEMS
        )
        or "+"
        in user_query
        or "*"
        in user_query
        or "^"
        in user_query
    ) and len(numbers) >= 2

    if is_math:

        math_matched = True

        op = "add"

        if (
            any(
                stem in query_lower
                for stem in [
                    "multipli",
                    "times",
                    "product"
                ]
            )
            or "*"
            in user_query
        ):

            op = "multiply"

        elif (
            "subtract"
            in query_lower
            or "minus"
            in query_lower
        ):

            op = "subtract"

        elif (
            "divid"
            in query_lower
            or "/"
            in user_query
        ):

            op = "divide"

        elif (
            "power"
            in query_lower
            or "^"
            in user_query
        ):

            op = "power"

        args_str = (
            f"operation='{op}', "
            f"a={numbers[0]}, "
            f"b={numbers[1]}"
        )

        print(
            "[+] MCP Agent: Calling FastMCP Tool "
            f"'calculate_math({args_str})'..."
        )

        result = calculate_math(
            op,
            numbers[0],
            numbers[1]
        )

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "calculate_math",
            "args": args_str,
            "result": result,
            "approval_required": False
        })


    # ======================================================
    # PRIME
    # ======================================================

    if "prime" in query_lower and numbers:

        number = int(numbers[0])

        args_str = f"number={number}"

        result = check_prime(number)

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "check_prime",
            "args": args_str,
            "result": result,
            "approval_required": False
        })


    # ======================================================
    # WEATHER
    # ======================================================

    if (
        "weather"
        in query_lower
        or "temperature"
        in query_lower
        or "climate"
        in query_lower
    ):

        city_match = re.search(
            r"(?:in|at|for)\s+"
            r"([A-Za-z]+(?:\s+[A-Za-z]+)*)",
            user_query,
            re.IGNORECASE
        )

        city = (
            city_match.group(1).strip()
            if city_match
            else "Delhi"
        )

        args_str = f"city='{city}'"

        print(
            "[+] MCP Agent: Calling FastMCP Tool "
            f"'check_weather({args_str})'..."
        )

        result = check_weather(city)

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "check_weather",
            "args": args_str,
            "result": result,
            "approval_required": True
        })


    # ======================================================
    # WEB TOPIC SEARCH
    # ======================================================

    is_web_query = (
        not math_matched
        and
        not (
            "weather" in query_lower
            or "temperature" in query_lower
            or "climate" in query_lower
        )
        and
        (
            "web" in query_lower
            or "search topic" in query_lower
            or "explain" in query_lower
            or (
                "what is" in query_lower
                and not numbers
            )
        )
    )

    if is_web_query:

        topic_match = re.search(
            r"(?:about|topic|is|explain)\s+"
            r"([A-Za-z\s]+)",
            user_query,
            re.IGNORECASE
        )

        target_topic = (
            topic_match.group(1).strip()
            if topic_match
            else user_query
        )

        args_str = f"topic='{target_topic}'"

        result = search_web_topic(
            target_topic
        )

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "search_web_topic",
            "args": args_str,
            "result": result,
            "approval_required": False
        })


    # ======================================================
    # GREETING
    # ======================================================

    if (
        "greet" in query_lower
        or "hi" in query_lower
        or "hello" in query_lower
    ):

        name_match = re.search(
            r"(?:name\s+is|i\s+am|greet)\s+"
            r"([A-Za-z]+)",
            user_query,
            re.IGNORECASE
        )

        user_name = (
            name_match.group(1)
            if name_match
            else "User"
        )

        result = greet_user(user_name)

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "greet_user",
            "args": f"name='{user_name}'",
            "result": result,
            "approval_required": False
        })


    # ======================================================
    # CANDIDATE SKILLS
    # ======================================================

    if (
        "skill" in query_lower
        or "framework" in query_lower
        or "database" in query_lower
    ):

        result = get_candidate_skills("all")

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "get_candidate_skills",
            "args": "category='all'",
            "result": result,
            "approval_required": False
        })


    # ======================================================
    # EXPERIENCE
    # ======================================================

    if (
        "experience" in query_lower
        or "duration" in query_lower
        or "how long" in query_lower
    ):

        start_year = (
            int(numbers[0])
            if len(numbers) >= 1
            and numbers[0] >= 2000
            else 2024
        )

        end_year = (
            int(numbers[1])
            if len(numbers) >= 2
            and numbers[1] >= 2000
            else 2026
        )

        result = calculate_experience(
            start_year,
            end_year
        )

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "calculate_experience",
            "args": (
                f"start={start_year}, "
                f"end={end_year}"
            ),
            "result": result,
            "approval_required": False
        })


    # ======================================================
    # CANDIDATE FIT
    # ======================================================

    if (
        "fit" in query_lower
        or "evaluate" in query_lower
        or "match" in query_lower
    ):

        result = evaluate_candidate_fit(
            "AI/ML Developer",
            "python, flask, qdrant, rag, mcp"
        )

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "evaluate_candidate_fit",
            "args": (
                "role='AI/ML Developer', "
                "skills='python, flask, qdrant, rag, mcp'"
            ),
            "result": result,
            "approval_required": False
        })


    # ======================================================
    # RESUME RAG FALLBACK
    # ======================================================

    if (
        not tool_outputs
        or "resume" in query_lower
        or "project" in query_lower
        or "internship" in query_lower
        or "anmol" in query_lower
    ):

        args_str = (
            f"query='{user_query[:60]}...', "
            "category='all'"
        )

        result = search_resume(
            user_query,
            "all"
        )

        tool_outputs.append(result)

        tool_calls_detail.append({
            "tool_name": "search_resume",
            "args": args_str,
            "result": result,
            "approval_required": False
        })


    # ======================================================
    # GEMINI SYNTHESIS
    # ======================================================

    key = get_gemini_key()

    if not key:

        return {
            "response": (
                "Gemini API key is not configured."
            ),
            "tools_discovered": tools_discovered,
            "tools_invoked": len(tool_outputs),
            "mcp_context": "\n\n".join(tool_outputs),
            "tool_calls_detail": tool_calls_detail
        }

    client = genai.Client(
        api_key=key
    )

    combined_context = "\n\n".join(
        tool_outputs
    )

    augmented_prompt = f"""
You are an intelligent FastMCP AI Agent.

Synthesize a concise, grounded and professional
response using the FastMCP tool outputs below.

Do not invent information that is not present
in the tool outputs.

FastMCP Server Tool Execution Outputs:

{combined_context}

User Query:
{user_query}

Grounded Answer:
"""

    models_to_try = [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-2.5-flash"
    ]

    response = None

    for model_name in models_to_try:

        try:

            response = client.models.generate_content(
                model=model_name,
                contents=augmented_prompt
            )

            break

        except Exception as error:

            print(
                f"[-] Gemini model '{model_name}' "
                f"unavailable. Trying fallback..."
            )

            continue


    if not response:

        return {
            "response": (
                "FastMCP Tool Execution Outputs:\n\n"
                f"{combined_context}"
            ),
            "tools_discovered": tools_discovered,
            "tools_invoked": len(tool_outputs),
            "mcp_context": combined_context,
            "tool_calls_detail": tool_calls_detail
        }


    return {
        "response": response.text,
        "tools_discovered": tools_discovered,
        "tools_invoked": len(tool_outputs),
        "mcp_context": combined_context,
        "tool_calls_detail": tool_calls_detail
    }


# ==========================================================
# LOCAL TEST
# ==========================================================

if __name__ == "__main__":

    result = run_mcp_query(
        "What is the weather in Mumbai?"
    )

    print(
        "=== UNIVERSAL MCP AGENT RESPONSE ==="
    )

    print(
        result["response"]
    )
