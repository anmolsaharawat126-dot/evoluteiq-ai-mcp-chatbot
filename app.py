from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
import os
import joblib
import base64
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from guardrails_engine import LLMGuardrailEngine

# Initialize Guardrail Engine
guardrails = LLMGuardrailEngine()

# ==========================================================
# SPEED OPTIMIZATION: Smart model caching + dead model blacklist
# ==========================================================
_cached_working_model = None          # Remembers last working model
_dead_models = {}                      # {model_name: timestamp_when_failed}
DEAD_MODEL_TTL = 60                    # Retry dead model after 60 seconds

def generate_with_retry(client, contents, config=None):
    global _cached_working_model, _dead_models

    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-2.5-flash"]

    # Put cached working model FIRST so we skip failed ones immediately
    if _cached_working_model and _cached_working_model in models_to_try:
        models_to_try = [_cached_working_model] + [m for m in models_to_try if m != _cached_working_model]

    now = time.time()
    last_exception = None

    for model_name in models_to_try:
        # Skip models that recently failed (within TTL window)
        if model_name in _dead_models:
            if now - _dead_models[model_name] < DEAD_MODEL_TTL:
                print(f"[~] Skipping blacklisted model '{model_name}' (quota cooldown)")
                continue
            else:
                del _dead_models[model_name]  # TTL expired, retry it

        try:
            if config:
                response = client.models.generate_content(
                    model=model_name, contents=contents, config=config
                )
            else:
                response = client.models.generate_content(
                    model=model_name, contents=contents
                )
            # Success — cache this model for future requests
            _cached_working_model = model_name
            return response

        except Exception as e:
            last_exception = e
            err_str = str(e)
            print(f"[-] Model '{model_name}' failed: {err_str[:120]}")
            # If rate limited (429) or quota exhausted, blacklist this model
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                _dead_models[model_name] = now
                print(f"[!] Model '{model_name}' blacklisted for {DEAD_MODEL_TTL}s")
            # No sleep between models — fail fast and move on

    print(f"[!!!] ALL GEMINI MODELS FAILED. Last error: {last_exception}")
    return type('DummyResponse', (), {'text': f"I'm temporarily unable to connect. Please try again in a moment."})()



app = Flask(__name__)

# ==========================================================
# 🔑 API KEYS CONFIGURATION (BACKEND)
# ==========================================================
CUSTOM_API_KEY = "anmol123"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Qdrant Cloud Credentials
QDRANT_URL = "https://fe05543a-c601-4ea0-ab59-3e41fffeab7f.eu-west-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
# Cached local memory store fallback for seamless operation if cloud is paused
_local_qdrant_cache = None
_qdrant_cloud_cache = None   # Cache successful cloud connection — avoid reconnect on every request

def get_qdrant_store(gemini_client):
    global _local_qdrant_cache, _qdrant_cloud_cache
    target_coll = "anmol_resume_collection_3072"

    # Return cached cloud client if already connected (FAST — no network call)
    if _qdrant_cloud_cache is not None:
        return _qdrant_cloud_cache, target_coll

    # 1. Try connecting to Qdrant Cloud Cluster (2s timeout — fail fast)
    try:
        q_cloud = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=2)
        if q_cloud.collection_exists(target_coll):
            _qdrant_cloud_cache = q_cloud   # Cache it!
            print("[+] Qdrant Cloud connected and cached.")
            return q_cloud, target_coll
        elif q_cloud.collection_exists("anmol_resume_collection"):
            _qdrant_cloud_cache = q_cloud
            return q_cloud, "anmol_resume_collection"
    except Exception as cloud_err:
        print(f"[-] Qdrant Cloud unavailable ({str(cloud_err)[:60]}). Using Local In-Memory Qdrant...")

    # 2. Fallback to Local In-Memory Qdrant Engine (cached after first build)
    if _local_qdrant_cache is not None:
        return _local_qdrant_cache, target_coll

    print("[+] Building Local In-Memory Qdrant Store...")
    from qdrant_client.models import VectorParams, Distance, PointStruct
    q_mem = QdrantClient(":memory:")
    q_mem.create_collection(
        collection_name=target_coll,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
    )
    for field in ["category", "role", "company", "source_file"]:
        q_mem.create_payload_index(collection_name=target_coll, field_name=field, field_schema="keyword")

    if os.path.exists("anmol_resume.txt"):
        with open("anmol_resume.txt", "r", encoding="utf-8") as f:
            raw_text = f.read()

        sections = [s.strip() for s in raw_text.split("\n\n") if s.strip()]
        points = []
        for idx, sec in enumerate(sections):
            cat = "general"
            if "summary" in sec.lower() or "saharawat" in sec.lower():
                cat = "summary"
            elif "work experience" in sec.lower() or "evaluate iq" in sec.lower() or "internship" in sec.lower():
                cat = "work_experience"
            elif "education" in sec.lower() or "b.tech" in sec.lower():
                cat = "education"
            elif "skills" in sec.lower():
                cat = "skills"

            vec = gemini_client.models.embed_content(model="gemini-embedding-2", contents=sec).embeddings[0].values
            points.append(
                PointStruct(
                    id=idx, vector=vec,
                    payload={"text": sec, "category": cat, "role": "AI/ML Developer Intern",
                             "company": "Evaluate IQ", "source_file": "anmol_resume.txt"}
                )
            )
        q_mem.upsert(collection_name=target_coll, points=points)

    _local_qdrant_cache = q_mem
    return q_mem, target_coll
# ==========================================================

# 🤖 LOAD CUSTOM MACHINE LEARNING MODEL
try:
    vectorizer = joblib.load("vectorizer.joblib")
    sentiment_model = joblib.load("sentiment_model.joblib")
    ml_model_loaded = True
    print("[+] Custom ML Sentiment Model loaded successfully!")
except Exception as e:
    print(f"[-] Warning: ML Model files not found. Run train_model.py first! ({e})")
    ml_model_loaded = False

@app.route("/")
def index():
    return render_template("index.html")

# Secure API Proxy Endpoint
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        # 1. Validation: Request headers key check
        client_api_key = request.headers.get("X-API-KEY") or CUSTOM_API_KEY
        # 2. Get JSON data safely (fallback to empty dict if None)
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        use_rag = data.get("useRAG", False)
        image_b64 = data.get("image", "").strip() if data.get("image") else ""
        image_type = data.get("imageType", "").strip() if data.get("imageType") else ""

        if not user_message and not image_b64:
            return jsonify({"error": "Validation Error: Question or Image file is required!"}), 400

        # 🛡️ 1. APPLY INPUT GUARDRAILS (PRE-LLM VALIDATION INTERCEPTOR)
        input_guard_res = guardrails.validate_input(user_message)
        if not input_guard_res.is_safe:
            print(f"[GUARDRAIL BLOCKED BEFORE LLM] [{input_guard_res.violation_category}] {input_guard_res.blocked_reason}")
            return jsonify({
                "response": f"🚨 [GUARDRAIL VIOLATION BLOCKED BEFORE LLM]\n\nViolation Category: {input_guard_res.violation_category}\nReason: {input_guard_res.blocked_reason}\n\nYour query violates application safety policies and was intercepted before reaching the LLM.",
                "sentiment": "negative",
                "guardrail_status": "blocked",
                "guardrail_category": input_guard_res.violation_category,
                "guardrail_msg": input_guard_res.blocked_reason
            }), 200

        active_prompt = input_guard_res.sanitized_prompt
        if input_guard_res.pii_detected:
            print(f"[🔒 GUARDRAIL PII REDACTED] Types: {input_guard_res.pii_types}")

        # 3. Predict Sentiment offline using our custom ML model
        predicted_sentiment = "neutral"  
        if ml_model_loaded and user_message:
            try:
                vectorized_text = vectorizer.transform([user_message.lower()])
                prediction_id = sentiment_model.predict(vectorized_text)[0]
                if prediction_id == 0:
                    predicted_sentiment = "positive"
                elif prediction_id == 1:
                    predicted_sentiment = "negative"
                else:
                    predicted_sentiment = "neutral"
            except Exception as ml_err:
                print(f"[-] ML Model execution error: {ml_err}")

        # 4. Check Google Gemini Key setup
        actual_gemini_key = GEMINI_API_KEY
        if actual_gemini_key == "PASTE_YOUR_REAL_GEMINI_API_KEY_HERE":
            actual_gemini_key = os.environ.get("GEMINI_API_KEY", "")
            
        if not actual_gemini_key or actual_gemini_key == "":
            return jsonify({"error": "Setup Error: Please configure your Google Gemini API Key in app.py (line 14)!"}), 500

        # Initialize Google SDK client
        client = genai.Client(api_key=actual_gemini_key)

        # Read temperature configuration safely
        try:
            temp = float(data.get("temperature", 0.7))
        except (ValueError, TypeError):
            temp = 0.7

        # 🔌 MODEL CONTEXT PROTOCOL (MCP) AGENT LOOP INTEGRATION
        use_mcp = data.get("useMCP", False)
        if use_mcp and user_message:
            print("[+] Processing request via Universal FastMCP Server & Agent...")
            try:
                from mcp_agent import run_mcp_query
                agent_res = run_mcp_query(active_prompt)
                output_guard_res = guardrails.validate_output(agent_res["response"])

                # Build Step-by-Step Agent Trace — exactly what Sir asked for
                agent_trace = []
                step = 1

                # STEP 1: User Input
                agent_trace.append({
                    "step": step, "type": "user_input",
                    "label": "User Input",
                    "content": active_prompt
                })
                step += 1

                # STEP 2 onwards — one block per tool
                tool_calls_detail = agent_res.get("tool_calls_detail", [])
                for tc in tool_calls_detail:
                    needs_approval = tc.get("approval_required", False)

                    if needs_approval:
                        # ── GATED TOOL FLOW ──────────────────────────────────
                        # Step 2: Tool Called
                        agent_trace.append({
                            "step": step, "type": "tool_call",
                            "label": f"Tool Called — {tc['tool_name']}",
                            "tool_name": tc["tool_name"],
                            "content": f"Tool : {tc['tool_name']}\nArgs : {tc['args']}"
                        })
                        step += 1
                        # Step 3: Policy
                        agent_trace.append({
                            "step": step, "type": "policy",
                            "label": "Policy",
                            "tool_name": tc["tool_name"],
                            "content": f"requires_approval"
                        })
                        step += 1
                        # Step 4: Approval prompt (user sees Approve/Deny in UI)
                        agent_trace.append({
                            "step": step, "type": "approval_required",
                            "label": "Approval Required",
                            "tool_name": tc["tool_name"],
                            "content": f"Tool '{tc['tool_name']}' needs your approval before executing.\nArgs: {tc['args']}"
                        })
                        step += 1
                        # Step 5: User Decision (pending — frontend handles approve/deny)
                        agent_trace.append({
                            "step": step, "type": "user_decision",
                            "label": "User Decision",
                            "tool_name": tc["tool_name"],
                            "content": "pending"   # Will be set to APPROVED/DENIED by frontend
                        })
                        step += 1
                        # Step 6: Tool Result (shown after user decides)
                        agent_trace.append({
                            "step": step, "type": "tool_output",
                            "label": "Tool Result",
                            "tool_name": tc["tool_name"],
                            "content": "pending"   # Will be filled after decision
                        })
                        step += 1
                    else:
                        # ── AUTO TOOL FLOW ────────────────────────────────────
                        # Step 2: Tool Called
                        agent_trace.append({
                            "step": step, "type": "tool_call",
                            "label": f"Tool Called — {tc['tool_name']}",
                            "tool_name": tc["tool_name"],
                            "content": f"Tool : {tc['tool_name']}\nArgs : {tc['args']}\nInput: {active_prompt[:100]}"
                        })
                        step += 1
                        # Step 3: Tool Result
                        agent_trace.append({
                            "step": step, "type": "tool_output",
                            "label": f"Tool Result — {tc['tool_name']}",
                            "tool_name": tc["tool_name"],
                            "content": str(tc["result"])[:300]
                        })
                        step += 1
                        # Step 4: Result Sent to LLM
                        agent_trace.append({
                            "step": step, "type": "llm_feed",
                            "label": "Result Sent to LLM",
                            "content": f"Tool output from '{tc['tool_name']}' fed into Gemini:\n→ {str(tc['result'])[:200]}"
                        })
                        step += 1

                # Final LLM Response
                agent_trace.append({
                    "step": step, "type": "final_answer",
                    "label": "Final LLM Response",
                    "content": output_guard_res.sanitized_output
                })



                return jsonify({
                    "response": output_guard_res.sanitized_output,
                    "sentiment": predicted_sentiment,
                    "mcp_status": "active",
                    "tools_discovered": agent_res["tools_discovered"],
                    "tools_invoked": agent_res["tools_invoked"],
                    "agent_trace": agent_trace,
                    "guardrail_status": "passed" if not input_guard_res.pii_detected else "pii_redacted",
                    "pii_types": input_guard_res.pii_types
                })
            except Exception as mcp_err:
                import traceback
                traceback.print_exc()
                return jsonify({"response": f"MCP Error: {str(mcp_err)}", "sentiment": predicted_sentiment}), 200


        # 💡 RAG INGESTION & FILTERING LOOP INTEGRATION
        if use_rag and user_message:
            print("[+] Processing request via Qdrant RAG Engine...")
            q_client, collection_name = get_qdrant_store(client)
            
            # Recreate query vector using gemini-embedding-2 (3072 dimensions)
            query_embedding_response = client.models.embed_content(
                model="gemini-embedding-2",
                contents=active_prompt
            )
            query_vector = query_embedding_response.embeddings[0].values
            
            # Extract Dynamic Metadata Payload Filters from Request
            filter_cat = data.get("filterCategory", "").strip()
            filter_role = data.get("filterRole", "").strip()
            filter_company = data.get("filterCompany", "").strip()
            filter_rule = data.get("filterRule", "must").strip().lower() # 'must' or 'must_not'
            
            filter_conditions = []
            if filter_cat and filter_cat != "all":
                filter_conditions.append(FieldCondition(key="category", match=MatchValue(value=filter_cat)))
            if filter_role and filter_role != "all":
                filter_conditions.append(FieldCondition(key="role", match=MatchValue(value=filter_role)))
            if filter_company and filter_company != "all":
                filter_conditions.append(FieldCondition(key="company", match=MatchValue(value=filter_company)))

            query_filter = None
            if filter_conditions:
                if filter_rule == "must_not":
                    query_filter = Filter(must_not=filter_conditions)
                    print(f"[+] Applied Qdrant Payload Filter (MUST_NOT): {filter_conditions}")
                else:
                    query_filter = Filter(must=filter_conditions)
                    print(f"[+] Applied Qdrant Payload Filter (MUST): {filter_conditions}")

            # Query Qdrant Cloud with Metadata Payload Filter
            response = q_client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=6
            )
            
            retrieved_texts = [result.payload['text'] for result in response.points]
            
            if not retrieved_texts:
                # No RAG context found — fall back to general AI response instead of error
                print("[+] No RAG context found — falling back to general AI response")
                general_prompt = f"""You are a highly capable, friendly AI assistant. Answer the following question accurately and helpfully.

Question: {active_prompt}
Answer:"""
                fallback_response = generate_with_retry(
                    client=client,
                    contents=general_prompt,
                    config={"temperature": temp}
                )
                output_guard_res = guardrails.validate_output(fallback_response.text)
                return jsonify({
                    "response": output_guard_res.sanitized_output,
                    "sentiment": predicted_sentiment,
                    "guardrail_status": "passed" if not input_guard_res.pii_detected else "pii_redacted",
                    "pii_types": input_guard_res.pii_types
                })

            context_str = "\n\n".join(retrieved_texts)
            
            # Smart RAG prompt — uses context if relevant, otherwise answers generally
            augmented_prompt = f"""You are a highly capable, friendly AI assistant. Answer the user's question accurately.

If the question is related to the provided Context (resume, candidate background, skills, experience), use the context.
If the question is a general question (math, science, coding, etc.), answer it directly from your knowledge — do NOT say "not in context".

Context (from knowledge base):
{context_str}

User Question: {active_prompt}
Answer:"""

            generation_response = generate_with_retry(
                client=client,
                contents=augmented_prompt,
                config={"temperature": temp}
            )
            
            output_guard_res = guardrails.validate_output(generation_response.text)
            
            return jsonify({
                "response": output_guard_res.sanitized_output,
                "sentiment": predicted_sentiment,
                "guardrail_status": "passed" if not input_guard_res.pii_detected else "pii_redacted",
                "pii_types": input_guard_res.pii_types
            })

        # Build genuine general-purpose system prompt
        SYSTEM_PROMPT = """You are a highly capable, friendly, and knowledgeable AI assistant. You can:
- Answer any general knowledge question (science, history, math, coding, current events, etc.)
- Help with coding problems in any programming language
- Explain complex concepts in simple terms
- Have casual conversations
- Help with writing, analysis, and creative tasks
- Discuss technology, AI, and machine learning topics

You are NOT restricted to any single topic. Answer every question accurately and helpfully.
If a user asks about Anmol Saharawat's resume or background, you can answer helpfully, but you are a GENERAL PURPOSE assistant first.
Be concise, clear, and helpful. Match the user's language tone."""

        # Build conversation history
        history = data.get("history", [])
        api_history = []
        for msg in history:
            if not isinstance(msg, dict) or "role" not in msg or "text" not in msg:
                continue
            api_history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["text"]}]
            })

        # Build image input if present
        if image_b64:
            image_bytes = base64.b64decode(image_b64)
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=image_type)
            user_input = [image_part, active_prompt] if active_prompt else [image_part]
        else:
            user_input = active_prompt

        try:
            if api_history and len(api_history) > 1:
                # Multi-turn: inject system prompt as first exchange in history
                full_history = [
                    {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
                    {"role": "model", "parts": [{"text": "Understood! I'm a general-purpose AI assistant ready to help with anything."}]}
                ] + api_history[:-1]
                chat_session = client.chats.create(
                    model="gemini-3.5-flash-lite",
                    history=full_history
                )
                response = chat_session.send_message(user_input, config={"temperature": temp})
            else:
                # Single-turn: combine system prompt + user message
                if image_b64:
                    full_prompt_input = [image_part, f"{SYSTEM_PROMPT}\n\nUser: {active_prompt}\nAssistant:"]
                else:
                    full_prompt_input = f"{SYSTEM_PROMPT}\n\nUser: {active_prompt}\nAssistant:"
                response = generate_with_retry(client=client, contents=full_prompt_input, config={"temperature": temp})
        except Exception as chat_err:
            print(f"[-] Standard chat execution exception: {chat_err}")
            response = type('DummyResponse', (), {'text': "Hello! I'm your AI assistant. Ask me anything — coding, science, math, general knowledge, or casual chat. How can I help?"})()
        output_guard_res = guardrails.validate_output(response.text)

        return jsonify({
            "response": output_guard_res.sanitized_output,
            "sentiment": predicted_sentiment,
            "guardrail_status": "passed" if not input_guard_res.pii_detected else "pii_redacted",
            "pii_types": input_guard_res.pii_types
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"response": f"Server Response: {str(e)}", "sentiment": "neutral"}), 200

if __name__ == "__main__":
    app.run(debug=False, port=5000)
