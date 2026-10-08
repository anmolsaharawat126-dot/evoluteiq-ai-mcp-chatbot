"""
=============================================================================
SMART DYNAMIC MCP AI AGENT (Universal FastMCP Tool Runner)
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
    search_resume,
    calculate_experience,
    get_candidate_skills,
    evaluate_candidate_fit
)

def get_gemini_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    try:
        if os.path.exists("app.py"):
            with open("app.py", "r", encoding="utf-8") as f:
                for line in f:
                    if "GEMINI_API_KEY =" in line and "PASTE_YOUR_REAL_GEMINI_API_KEY_HERE" not in line:
                        extracted_key = line.split("=")[1].strip().strip('"').strip("'")
                        if extracted_key:
                            return extracted_key
    except Exception as e:
        print(f"[-] Warning: {e}")
    return ""

def run_mcp_query(user_query: str) -> dict:
    """
    Discovers all FastMCP tools and dynamically routes user prompts to matching tools.
    """
    tools_discovered = [
        "greet_user", "calculate_math", "check_prime",
        "search_web_topic", "search_resume", "calculate_experience",
        "get_candidate_skills", "evaluate_candidate_fit", "delete_file"
    ]

    query_lower = user_query.lower()
    tool_outputs = []
    tool_calls_detail = []
    math_matched = False   # If math fires, block search_web_topic (avoid wrong routing)

    # ── MATH STEMS: "multiply" is NOT a substring of "multiplied" ────────────
    # Fix: use stem matching — "multipli" matches multiply/multiplied/multiplication
    # Same fix for "divid" (divide/divided/division) and "subtract" (subtracted)
    MATH_STEMS = ["add", "plus", "sum", "multipli", "times", "divid",
                  "subtract", "minus", "calculate", "math", "product"]

    # 1. Math Calculation Tool
    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", user_query)]
    is_math = (
        any(stem in query_lower for stem in MATH_STEMS) or
        "+" in user_query or "*" in user_query
    ) and len(numbers) >= 2

    if is_math:
        math_matched = True
        op = "add"
        if any(s in query_lower for s in ["multipli", "times", "product"]) or "*" in user_query:
            op = "multiply"
        elif any(s in query_lower for s in ["subtract", "minus"]):
            op = "subtract"
        elif "divid" in query_lower or "/" in user_query:
            op = "divide"
        args_str = f"op='{op}', a={numbers[0]}, b={numbers[1]}"
        print(f"[+] MCP Agent: Calling FastMCP Tool 'calculate_math({args_str})'...")
        result = calculate_math(op, numbers[0], numbers[1])
        tool_outputs.append(result)
        tool_calls_detail.append({
            "tool_name": "calculate_math",
            "args": args_str,
            "result": result,
            "approval_required": False
        })

    # 2. Prime Check Tool
    if "prime" in query_lower and numbers:
        int_val = int(numbers[0])
        args_str = f"number={int_val}"
        print(f"[+] MCP Agent: Calling FastMCP Tool 'check_prime({int_val})'...")
        result = check_prime(int_val)
        tool_outputs.append(result)
        tool_calls_detail.append({"tool_name": "check_prime", "args": args_str, "result": result, "approval_required": False})

    # 3. Web Topic Search Tool
    # IMPORTANT: Skip if math routing already fired — prevents "What is 15*20?"
    # from going to search_web_topic when calculate_math is the correct tool.
    is_web_query = (
        not math_matched and (
            "web" in query_lower or "search topic" in query_lower or
            "explain" in query_lower or
            ("what is" in query_lower and not numbers)  # "what is" only if no numbers
        )
    )
    if is_web_query:
        topic_match = re.search(r"(?:about|topic|is|explain)\s+([A-Za-z\s]+)", user_query, re.IGNORECASE)
        target_topic = topic_match.group(1).strip() if topic_match else user_query
        args_str = f"topic='{target_topic}'"
        print(f"[+] MCP Agent: Calling FastMCP Tool 'search_web_topic({args_str})'...")
        result = search_web_topic(target_topic)
        tool_outputs.append(result)
        tool_calls_detail.append({"tool_name": "search_web_topic", "args": args_str, "result": result, "approval_required": False})

    # 4. Greeting Tool
    if "greet" in query_lower or "hi" in query_lower or "hello" in query_lower:
        name_match = re.search(r"(?:name\s+is|i\s+am|greet)\s+([A-Za-z]+)", user_query, re.IGNORECASE)
        user_name = name_match.group(1) if name_match else "User"
        args_str = f"name='{user_name}'"
        print(f"[+] MCP Agent: Calling FastMCP Tool 'greet_user({args_str})'...")
        result = greet_user(user_name)
        tool_outputs.append(result)
        tool_calls_detail.append({"tool_name": "greet_user", "args": args_str, "result": result, "approval_required": False})

    # 5. Candidate Skills Tool
    if "skill" in query_lower or "framework" in query_lower or "database" in query_lower:
        args_str = "category='all'"
        print("[+] MCP Agent: Calling FastMCP Tool 'get_candidate_skills'...")
        result = get_candidate_skills("all")
        tool_outputs.append(result)
        tool_calls_detail.append({"tool_name": "get_candidate_skills", "args": args_str, "result": result, "approval_required": False})

    # 6. Experience Calculator Tool
    if "experience" in query_lower or "duration" in query_lower or "how long" in query_lower:
        start_y = int(numbers[0]) if len(numbers) >= 1 and numbers[0] >= 2000 else 2024
        end_y = int(numbers[1]) if len(numbers) >= 2 and numbers[1] >= 2000 else 2026
        args_str = f"start={start_y}, end={end_y}"
        print(f"[+] MCP Agent: Calling FastMCP Tool 'calculate_experience({args_str})'...")
        result = calculate_experience(start_y, end_y)
        tool_outputs.append(result)
        tool_calls_detail.append({"tool_name": "calculate_experience", "args": args_str, "result": result, "approval_required": False})

    # 7. Candidate Fit Assessment Tool
    if "fit" in query_lower or "evaluate" in query_lower or "match" in query_lower:
        args_str = "role='AI/ML Developer', skills='python, flask, qdrant, rag, mcp'"
        print("[+] MCP Agent: Calling FastMCP Tool 'evaluate_candidate_fit'...")
        result = evaluate_candidate_fit("AI/ML Developer", "python, flask, qdrant, rag, mcp")
        tool_outputs.append(result)
        tool_calls_detail.append({"tool_name": "evaluate_candidate_fit", "args": args_str, "result": result, "approval_required": False})

    # 8. Delete File Tool — GATED (requires_approval=True)
    # Marks the tool call as requiring approval; actual approval UI is in app.py
    if "delete" in query_lower or "remove file" in query_lower or "erase" in query_lower:
        filename_match = re.search(r"(?:delete|remove|erase)\s+([\w.\-]+)", user_query, re.IGNORECASE)
        filename = filename_match.group(1) if filename_match else "unknown_file"
        args_str = f"filename='{filename}'"
        print(f"[+] MCP Agent: Gated tool 'delete_file({args_str})' — approval required in UI")
        # Don't execute — just flag for approval in the trace
        tool_calls_detail.append({
            "tool_name": "delete_file",
            "args": args_str,
            "result": None,           # Result pending approval
            "approval_required": True  # UI will show approve/deny buttons
        })

    # 9. Resume Vector RAG Tool (fallback if nothing matched)
    if not tool_outputs or "resume" in query_lower or "project" in query_lower or "internship" in query_lower:
        args_str = f"query='{user_query[:60]}...', category='all'"
        print("[+] MCP Agent: Calling FastMCP Tool 'search_resume'...")
        result = search_resume(user_query, "all")
        tool_outputs.append(result)
        tool_calls_detail.append({"tool_name": "search_resume", "args": args_str, "result": result, "approval_required": False})

    # Synthesize grounded answer using Gemini API with automatic fallback models
    key = get_gemini_key()
    client = genai.Client(api_key=key)

    combined_context = "\n\n".join(tool_outputs)
    augmented_prompt = f"""You are an intelligent FastMCP AI Agent. Synthesize a concise, grounded, and professional response to the user's query using strictly the tool outputs from the FastMCP Server.

FastMCP Server Tool Execution Outputs:
{combined_context}

User Query: {user_query}
Grounded Answer:"""

    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-2.5-flash"]
    response = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(model=model_name, contents=augmented_prompt)
            break
        except Exception as err:
            print(f"[-] Gemini model '{model_name}' rate limited/unavailable. Retrying with fallback model...")
            continue

    if not response:
        return {
            "response": f"FastMCP Tool Execution Outputs:\n\n{combined_context}",
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
        "tool_calls_detail": tool_calls_detail   # NEW: exact per-tool info for trace
    }


if __name__ == "__main__":
    res = run_mcp_query("Greet Anmol, calculate 15 multiplied by 8, and explain topic machine learning")
    print("=== UNIVERSAL MCP AGENT RESPONSE ===")
    print(res["response"])
