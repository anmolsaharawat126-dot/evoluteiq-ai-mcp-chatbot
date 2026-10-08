from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types
import os
import joblib
import base64
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from guardrails_engine import LLMGuardrailEngine

guardrails = LLMGuardrailEngine()

_cached_working_model = None
_dead_models = {}
DEAD_MODEL_TTL = 60

def generate_with_retry(client, contents, config=None):
global _cached_working_model, _dead_models

```
models_to_try = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash"
]

if _cached_working_model and _cached_working_model in models_to_try:
    models_to_try = (
        [_cached_working_model]
        + [m for m in models_to_try if m != _cached_working_model]
    )

now = time.time()
last_exception = None

for model_name in models_to_try:

    if model_name in _dead_models:
        if now - _dead_models[model_name] < DEAD_MODEL_TTL:
            print(
                f"[~] Skipping blacklisted model "
                f"'{model_name}' (quota cooldown)"
            )
            continue
        else:
            del _dead_models[model_name]

    try:
        if config:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
        else:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )

        _cached_working_model = model_name
        return response

    except Exception as e:
        last_exception = e
        err_str = str(e)

        print(
            f"[-] Model '{model_name}' failed: "
            f"{err_str[:120]}"
        )

        if (
            "429" in err_str
            or "RESOURCE_EXHAUSTED" in err_str
            or "quota" in err_str.lower()
        ):
            _dead_models[model_name] = now
            print(
                f"[!] Model '{model_name}' blacklisted "
                f"for {DEAD_MODEL_TTL}s"
            )

print(
    f"[!!!] ALL GEMINI MODELS FAILED. "
    f"Last error: {last_exception}"
)

return type(
    "DummyResponse",
    (),
    {
        "text": (
            "I'm temporarily unable to connect. "
            "Please try again in a moment."
        )
    }
)()
```

app = Flask(**name**)

# Enable CORS so the Vercel frontend can call the Render backend.

CORS(app)

CUSTOM_API_KEY = "anmol123"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

QDRANT_URL = (
"https://fe05543a-c601-4ea0-ab59-3e41fffeab7f."
"eu-west-1-0.aws.cloud.qdrant.io"
)

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

_local_qdrant_cache = None
_qdrant_cloud_cache = None

def get_qdrant_store(gemini_client):

```
global _local_qdrant_cache, _qdrant_cloud_cache

target_coll = "anmol_resume_collection_3072"

if _qdrant_cloud_cache is not None:
    return _qdrant_cloud_cache, target_coll

try:

    q_cloud = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=2
    )

    if q_cloud.collection_exists(target_coll):

        _qdrant_cloud_cache = q_cloud

        print("[+] Qdrant Cloud connected and cached.")

        return q_cloud, target_coll

    elif q_cloud.collection_exists(
        "anmol_resume_collection"
    ):

        _qdrant_cloud_cache = q_cloud

        return q_cloud, "anmol_resume_collection"

except Exception as cloud_err:

    print(
        "[-] Qdrant Cloud unavailable "
        f"({str(cloud_err)[:60]}). "
        "Using Local In-Memory Qdrant..."
    )

if _local_qdrant_cache is not None:
    return _local_qdrant_cache, target_coll

print("[+] Building Local In-Memory Qdrant Store...")

from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct
)

q_mem = QdrantClient(":memory:")

q_mem.create_collection(
    collection_name=target_coll,
    vectors_config=VectorParams(
        size=3072,
        distance=Distance.COSINE
    )
)

for field in [
    "category",
    "role",
    "company",
    "source_file"
]:

    q_mem.create_payload_index(
        collection_name=target_coll,
        field_name=field,
        field_schema="keyword"
    )

if os.path.exists("anmol_resume.txt"):

    with open(
        "anmol_resume.txt",
        "r",
        encoding="utf-8"
    ) as f:

        raw_text = f.read()

    sections = [
        s.strip()
        for s in raw_text.split("\n\n")
        if s.strip()
    ]

    points = []

    for idx, sec in enumerate(sections):

        cat = "general"

        if (
            "summary" in sec.lower()
            or "saharawat" in sec.lower()
        ):

            cat = "summary"

        elif (
            "work experience" in sec.lower()
            or "evaluate iq" in sec.lower()
            or "internship" in sec.lower()
        ):

            cat = "work_experience"

        elif (
            "education" in sec.lower()
            or "b.tech" in sec.lower()
        ):

            cat = "education"

        elif "skills" in sec.lower():

            cat = "skills"

        vec = (
            gemini_client
            .models
            .embed_content(
                model="gemini-embedding-2",
                contents=sec
            )
            .embeddings[0]
            .values
        )

        points.append(
            PointStruct(
                id=idx,
                vector=vec,
                payload={
                    "text": sec,
                    "category": cat,
                    "role": "AI/ML Developer Intern",
                    "company": "Evaluate IQ",
                    "source_file": "anmol_resume.txt"
                }
            )
        )

    q_mem.upsert(
        collection_name=target_coll,
        points=points
    )

_local_qdrant_cache = q_mem

return q_mem, target_coll
```

try:

```
vectorizer = joblib.load(
    "vectorizer.joblib"
)

sentiment_model = joblib.load(
    "sentiment_model.joblib"
)

ml_model_loaded = True

print(
    "[+] Custom ML Sentiment Model "
    "loaded successfully!"
)
```

except Exception as e:

```
print(
    "[-] Warning: ML Model files not found. "
    f"Run train_model.py first! ({e})"
)

ml_model_loaded = False
```

@app.route("/")
def index():

```
return render_template("index.html")
```

@app.route("/api/chat", methods=["POST"])
def chat():

```
try:

    client_api_key = (
        request.headers.get("X-API-KEY")
        or CUSTOM_API_KEY
    )

    data = request.get_json() or {}

    user_message = (
        data.get("message", "")
        .strip()
    )

    use_rag = data.get(
        "useRAG",
        False
    )

    image_b64 = (
        data.get("image", "").strip()
        if data.get("image")
        else ""
    )

    image_type = (
        data.get("imageType", "").strip()
        if data.get("imageType")
        else ""
    )

    if not user_message and not image_b64:

        return jsonify(
            {
                "error": (
                    "Validation Error: "
                    "Question or Image file "
                    "is required!"
                )
            }
        ), 400

    input_guard_res = (
        guardrails.validate_input(
            user_message
        )
    )

    if not input_guard_res.is_safe:

        print(
            "[GUARDRAIL BLOCKED BEFORE LLM] "
            f"[{input_guard_res.violation_category}] "
            f"{input_guard_res.blocked_reason}"
        )

        return jsonify(
            {
                "response": (
                    "🚨 [GUARDRAIL VIOLATION "
                    "BLOCKED BEFORE LLM]\n\n"
                    f"Violation Category: "
                    f"{input_guard_res.violation_category}\n"
                    f"Reason: "
                    f"{input_guard_res.blocked_reason}\n\n"
                    "Your query violates application "
                    "safety policies and was intercepted "
                    "before reaching the LLM."
                ),
                "sentiment": "negative",
                "guardrail_status": "blocked",
                "guardrail_category":
                    input_guard_res.violation_category,
                "guardrail_msg":
                    input_guard_res.blocked_reason
            }
        ), 200

    active_prompt = (
        input_guard_res.sanitized_prompt
    )

    if input_guard_res.pii_detected:

        print(
            "[GUARDRAIL PII REDACTED] "
            f"Types: "
            f"{input_guard_res.pii_types}"
        )

    predicted_sentiment = "neutral"

    if ml_model_loaded and user_message:

        try:

            vectorized_text = (
                vectorizer.transform(
                    [user_message.lower()]
                )
            )

            prediction_id = (
                sentiment_model.predict(
                    vectorized_text
                )[0]
            )

            if prediction_id == 0:
                predicted_sentiment = "positive"

            elif prediction_id == 1:
                predicted_sentiment = "negative"

            else:
                predicted_sentiment = "neutral"

        except Exception as ml_err:

            print(
                "[-] ML Model execution error: "
                f"{ml_err}"
            )

    actual_gemini_key = GEMINI_API_KEY

    if (
        actual_gemini_key
        == "PASTE_YOUR_REAL_GEMINI_API_KEY_HERE"
    ):

        actual_gemini_key = os.environ.get(
            "GEMINI_API_KEY",
            ""
        )

    if not actual_gemini_key:

        return jsonify(
            {
                "error": (
                    "Setup Error: Please configure "
                    "your Google Gemini API Key."
                )
            }
        ), 500

    client = genai.Client(
        api_key=actual_gemini_key
    )

    try:

        temp = float(
            data.get(
                "temperature",
                0.7
            )
        )

    except (
        ValueError,
        TypeError
    ):

        temp = 0.7

    use_mcp = data.get(
        "useMCP",
        False
    )

    if use_mcp and user_message:

        print(
            "[+] Processing request via "
            "Universal FastMCP Server & Agent..."
        )

        try:

            from mcp_agent import run_mcp_query

            agent_res = run_mcp_query(
                active_prompt
            )

            output_guard_res = (
                guardrails.validate_output(
                    agent_res["response"]
                )
            )

            agent_trace = []

            step = 1

            agent_trace.append(
                {
                    "step": step,
                    "type": "user_input",
                    "label": "User Input",
                    "content": active_prompt
                }
            )

            step += 1

            tool_calls_detail = agent_res.get(
                "tool_calls_detail",
                []
            )

            for tc in tool_calls_detail:

                needs_approval = tc.get(
                    "approval_required",
                    False
                )

                if needs_approval:

                    agent_trace.append(
                        {
                            "step": step,
                            "type": "tool_call",
                            "label":
                                f"Tool Called — "
                                f"{tc['tool_name']}",
                            "tool_name":
                                tc["tool_name"],
                            "content":
                                f"Tool : "
                                f"{tc['tool_name']}\n"
                                f"Args : "
                                f"{tc['args']}"
                        }
                    )

                    step += 1

                    agent_trace.append(
                        {
                            "step": step,
                            "type": "policy",
                            "label": "Policy",
                            "tool_name":
                                tc["tool_name"],
                            "content":
                                "requires_approval"
                        }
                    )

                    step += 1

                    agent_trace.append(
                        {
                            "step": step,
                            "type":
                                "approval_required",
                            "label":
                                "Approval Required",
                            "tool_name":
                                tc["tool_name"],
                            "content":
                                (
                                    f"Tool "
                                    f"'{tc['tool_name']}' "
                                    "needs your approval "
                                    "before executing.\n"
                                    f"Args: {tc['args']}"
                                )
                        }
                    )

                    step += 1

                    agent_trace.append(
                        {
                            "step": step,
                            "type":
                                "user_decision",
                            "label":
                                "User Decision",
                            "tool_name":
                                tc["tool_name"],
                            "content":
                                "pending"
                        }
                    )

                    step += 1

                    agent_trace.append(
                        {
                            "step": step,
                            "type":
                                "tool_output",
                            "label":
                                "Tool Result",
                            "tool_name":
                                tc["tool_name"],
                            "content":
                                "pending"
                        }
                    )

                    step += 1

                else:

                    agent_trace.append(
                        {
                            "step": step,
                            "type":
                                "tool_call",
                            "label":
                                f"Tool Called — "
                                f"{tc['tool_name']}",
                            "tool_name":
                                tc["tool_name"],
                            "content":
                                (
                                    f"Tool : "
                                    f"{tc['tool_name']}\n"
                                    f"Args : "
                                    f"{tc['args']}\n"
                                    f"Input: "
                                    f"{active_prompt[:100]}"
                                )
                        }
                    )

                    step += 1

                    agent_trace.append(
                        {
                            "step": step,
                            "type":
                                "tool_output",
                            "label":
                                f"Tool Result — "
                                f"{tc['tool_name']}",
                            "tool_name":
                                tc["tool_name"],
                            "content":
                                str(
                                    tc["result"]
                                )[:300]
                        }
                    )

                    step += 1

                    agent_trace.append(
                        {
                            "step": step,
                            "type":
                                "llm_feed",
                            "label":
                                "Result Sent to LLM",
                            "content":
                                (
                                    f"Tool output from "
                                    f"'{tc['tool_name']}' "
                                    "fed into Gemini:\n"
                                    f"→ {str(tc['result'])[:200]}"
                                )
                        }
                    )

                    step += 1

            agent_trace.append(
                {
                    "step": step,
                    "type": "final_answer",
                    "label": "Final LLM Response",
                    "content":
                        output_guard_res.sanitized_output
                }
            )

            return jsonify(
                {
                    "response":
                        output_guard_res.sanitized_output,
                    "sentiment":
                        predicted_sentiment,
                    "mcp_status":
                        "active",
                    "tools_discovered":
                        agent_res["tools_discovered"],
                    "tools_invoked":
                        agent_res["tools_invoked"],
                    "agent_trace":
                        agent_trace,
                    "guardrail_status":
                        (
                            "passed"
                            if not input_guard_res.pii_detected
                            else "pii_redacted"
                        ),
                    "pii_types":
                        input_guard_res.pii_types
                }
            )

        except Exception as mcp_err:

            import traceback

            traceback.print_exc()

            return jsonify(
                {
                    "response":
                        f"MCP Error: {str(mcp_err)}",
                    "sentiment":
                        predicted_sentiment
                }
            ), 200

    if use_rag and user_message:

        print(
            "[+] Processing request via "
            "Qdrant RAG Engine..."
        )

        q_client, collection_name = (
            get_qdrant_store(client)
        )

        query_embedding_response = (
            client.models.embed_content(
                model="gemini-embedding-2",
                contents=active_prompt
            )
        )

        query_vector = (
            query_embedding_response
            .embeddings[0]
            .values
        )

        filter_cat = data.get(
            "filterCategory",
            ""
        ).strip()

        filter_role = data.get(
            "filterRole",
            ""
        ).strip()

        filter_company = data.get(
            "filterCompany",
            ""
        ).strip()

        filter_rule = data.get(
            "filterRule",
            "must"
        ).strip().lower()

        filter_conditions = []

        if (
            filter_cat
            and filter_cat != "all"
        ):

            filter_conditions.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(
                        value=filter_cat
                    )
                )
            )

        if (
            filter_role
            and filter_role != "all"
        ):

            filter_conditions.append(
                FieldCondition(
                    key="role",
                    match=MatchValue(
                        value=filter_role
                    )
                )
            )

        if (
            filter_company
            and filter_company != "all"
        ):

            filter_conditions.append(
                FieldCondition(
                    key="company",
                    match=MatchValue(
                        value=filter_company
                    )
                )
            )

        query_filter = None

        if filter_conditions:

            if filter_rule == "must_not":

                query_filter = Filter(
                    must_not=filter_conditions
                )

            else:

                query_filter = Filter(
                    must=filter_conditions
                )

        response = q_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=6
        )

        retrieved_texts = [
            result.payload["text"]
            for result in response.points
        ]

        if not retrieved_texts:

            general_prompt = f"""
```

You are a highly capable, friendly AI assistant.
Answer the following question accurately and helpfully.

Question: {active_prompt}

Answer:
"""

```
            fallback_response = generate_with_retry(
                client=client,
                contents=general_prompt,
                config={
                    "temperature": temp
                }
            )

            output_guard_res = (
                guardrails.validate_output(
                    fallback_response.text
                )
            )

            return jsonify(
                {
                    "response":
                        output_guard_res.sanitized_output,
                    "sentiment":
                        predicted_sentiment,
                    "guardrail_status":
                        (
                            "passed"
                            if not input_guard_res.pii_detected
                            else "pii_redacted"
                        ),
                    "pii_types":
                        input_guard_res.pii_types
                }
            )

        context_str = "\n\n".join(
            retrieved_texts
        )

        augmented_prompt = f"""
```

You are a highly capable, friendly AI assistant.
Answer the user's question accurately.

If the question is related to the provided Context
(resume, candidate background, skills, experience),
use the context.

If the question is a general question
(math, science, coding, etc.), answer it directly
from your knowledge — do NOT say "not in context".

Context (from knowledge base):

{context_str}

User Question: {active_prompt}

Answer:
"""

```
        generation_response = generate_with_retry(
            client=client,
            contents=augmented_prompt,
            config={
                "temperature": temp
            }
        )

        output_guard_res = (
            guardrails.validate_output(
                generation_response.text
            )
        )

        return jsonify(
            {
                "response":
                    output_guard_res.sanitized_output,
                "sentiment":
                    predicted_sentiment,
                "guardrail_status":
                    (
                        "passed"
                        if not input_guard_res.pii_detected
                        else "pii_redacted"
                    ),
                "pii_types":
                    input_guard_res.pii_types
            }
        )

    SYSTEM_PROMPT = """
```

You are a highly capable, friendly, and knowledgeable
AI assistant.

You can:

* Answer general knowledge questions
* Answer science questions
* Answer history questions
* Solve math problems
* Help with coding
* Explain complex concepts simply
* Have casual conversations
* Help with writing
* Help with analysis
* Help with creative tasks
* Discuss technology, AI and machine learning

You are NOT restricted to any single topic.

If a user asks about Anmol Saharawat's resume
or background, answer helpfully.

You are a GENERAL PURPOSE assistant first.

Be concise, clear and helpful.
Match the user's language tone.
"""

```
    history = data.get(
        "history",
        []
    )

    api_history = []

    for msg in history:

        if (
            not isinstance(msg, dict)
            or "role" not in msg
            or "text" not in msg
        ):
            continue

        api_history.append(
            {
                "role":
                    (
                        "user"
                        if msg["role"] == "user"
                        else "model"
                    ),
                "parts":
                    [
                        {
                            "text":
                                msg["text"]
                        }
                    ]
            }
        )

    if image_b64:

        image_bytes = base64.b64decode(
            image_b64
        )

        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=image_type
        )

        user_input = (
            [image_part, active_prompt]
            if active_prompt
            else [image_part]
        )

    else:

        user_input = active_prompt

    try:

        if (
            api_history
            and len(api_history) > 1
        ):

            full_history = [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text":
                                SYSTEM_PROMPT
                        }
                    ]
                },
                {
                    "role": "model",
                    "parts": [
                        {
                            "text":
                                (
                                    "Understood! "
                                    "I'm a general-purpose "
                                    "AI assistant ready to "
                                    "help with anything."
                                )
                        }
                    ]
                }
            ] + api_history[:-1]

            chat_session = client.chats.create(
                model="gemini-3.5-flash-lite",
                history=full_history
            )

            response = chat_session.send_message(
                user_input,
                config={
                    "temperature": temp
                }
            )

        else:

            if image_b64:

                full_prompt_input = [
                    image_part,
                    (
                        f"{SYSTEM_PROMPT}\n\n"
                        f"User: {active_prompt}\n"
                        "Assistant:"
                    )
                ]

            else:

                full_prompt_input = (
                    f"{SYSTEM_PROMPT}\n\n"
                    f"User: {active_prompt}\n"
                    "Assistant:"
                )

            response = generate_with_retry(
                client=client,
                contents=full_prompt_input,
                config={
                    "temperature": temp
                }
            )

    except Exception as chat_err:

        print(
            "[-] Standard chat execution "
            f"exception: {chat_err}"
        )

        response = type(
            "DummyResponse",
            (),
            {
                "text":
                    (
                        "Hello! I'm your AI assistant. "
                        "Ask me anything — coding, science, "
                        "math, general knowledge, or casual "
                        "chat. How can I help?"
                    )
            }
        )()

    output_guard_res = (
        guardrails.validate_output(
            response.text
        )
    )

    return jsonify(
        {
            "response":
                output_guard_res.sanitized_output,
            "sentiment":
                predicted_sentiment,
            "guardrail_status":
                (
                    "passed"
                    if not input_guard_res.pii_detected
                    else "pii_redacted"
                ),
            "pii_types":
                input_guard_res.pii_types
        }
    )

except Exception as e:

    import traceback

    traceback.print_exc()

    return jsonify(
        {
            "response":
                f"Server Response: {str(e)}",
            "sentiment":
                "neutral"
        }
    ), 200
```

if **name** == "**main**":

```
app.run(
    debug=False,
    port=5000
)
```
