import re
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ==========================================================
# 🛡️ GUARDRAILS ENGINE RESULT DATACLASSES
# ==========================================================

@dataclass
class InputGuardrailResult:
    is_safe: bool
    blocked_reason: Optional[str]
    violation_category: Optional[str]
    sanitized_prompt: str
    pii_detected: bool
    pii_types: List[str]

@dataclass
class OutputGuardrailResult:
    is_safe: bool
    blocked_reason: Optional[str]
    sanitized_output: str

# ==========================================================
# 🛡️ LLM GUARDRAIL ENGINE CLASS
# ==========================================================

class LLMGuardrailEngine:
    def __init__(self):
        # 1. Adversarial Jailbreak & Prompt Injection Patterns
        self.jailbreak_patterns = [
            (r"ignore\s+(all\s+)?(previous\s+)?instructions", "Jailbreak / Prompt Injection"),
            (r"disregard\s+(all\s+)?prior\s+rules", "Jailbreak / Prompt Injection"),
            (r"bypass\s+safety", "Jailbreak / Prompt Injection"),
            (r"override\s+system", "Jailbreak / Prompt Injection"),
            (r"system\s+prompt", "Jailbreak / Prompt Injection"),
            (r"reveal\s+secret", "Jailbreak / Prompt Injection"),
            (r"dan\s+mode", "Jailbreak / Prompt Injection"),
            (r"do\s+anything\s+now", "Jailbreak / Prompt Injection"),
            (r"act\s+as\s+(an\s+)?unrestricted", "Jailbreak / Prompt Injection"),
            (r"pretend\s+you\s+have\s+no\s+rules", "Jailbreak / Prompt Injection"),
            (r"you\s+are\s+now\s+in\s+developer\s+mode", "Jailbreak / Prompt Injection")
        ]
        
        # 2. Comprehensive Categorized Threat Taxonomy (General Harmful Intent)
        self.harmful_categories = {
            "Theft & Robbery": [
                r"rob\s+(a\s+)?bank", r"robbing\s+(a\s+)?bank", r"bank\s+robbery",
                r"steal\s+money", r"how\s+to\s+steal", r"heist\s+plan", r"pickpocket",
                r"shoplift", r"break\s+into\s+bank", r"bank\s+heist"
            ],
            "Violence & Homicide": [
                r"kill\s+(a\s+)?person", r"kill\s+someone", r"kill\s+(a\s+)?human",
                r"murder\s+(a\s+)?person", r"murder\s+someone", r"how\s+to\s+kill",
                r"stab\s+someone", r"shoot\s+someone", r"strangle", r"assassinate"
            ],
            "Animal Cruelty & Harm": [
                r"kill\s+(an\s+)?animal", r"kill\s+animals", r"torture\s+animal",
                r"harm\s+animal", r"animal\s+abuse", r"animal\s+cruelty", r"abuse\s+pets"
            ],
            "Weapons & Explosives / Illegal Acts": [
                r"make\s+(a\s+)?bomb", r"build\s+(an\s+)?explosive", r"manufacture\s+weapon",
                r"illegal\s+act", r"poison\s+someone", r"make\s+illegal\s+drug", r"synthesize\s+drug"
            ],
            "Cybercrime & Hacking": [
                r"hack\s+database", r"steal\s+credentials", r"bypass\s+password",
                r"inject\s+malware", r"ddos\s+attack", r"phishing\s+attack", r"cyberattack"
            ],
            "Harassment & Hate Speech": [
                r"generate\s+hate\s+speech", r"harass\s+person", r"abusive\s+content",
                r"racial\s+slur", r"hate\s+crime"
            ],
            "Self-Harm & Suicide": [
                r"suicide\s+instruction", r"how\s+to\s+commit\s+suicide", r"self\s+harm",
                r"end\s+my\s+life", r"cut\s+myself"
            ]
        }
        
        # 3. PII Regex Patterns
        self.pii_patterns = {
            "EMAIL": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]"),
            "PHONE": (r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]"),
            "CREDIT_CARD": (r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CARD]"),
            "API_KEY": (r"\b(AIzaSy[a-zA-Z0-9_-]{33}|eyJ[a-zA-Z0-9_-]{30,})\b", "[REDACTED_API_KEY]"),
            "SSN": (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]")
        }

    # ==========================================================
    # 🔍 INPUT GUARDRAILS (Pre-LLM Processing Interceptor)
    # ==========================================================
    def validate_input(self, user_prompt: str) -> InputGuardrailResult:
        prompt_lower = user_prompt.lower().strip()
        
        # Rail 1: Jailbreak & Prompt Injection Check
        for pattern, cat in self.jailbreak_patterns:
            if re.search(pattern, prompt_lower):
                return InputGuardrailResult(
                    is_safe=False,
                    blocked_reason=f"Adversarial Prompt Injection Detected (Pattern: '{pattern}')",
                    violation_category=cat,
                    sanitized_prompt=user_prompt,
                    pii_detected=False,
                    pii_types=[]
                )
                
        # Rail 2: General Harmful Content Check (Theft, Violence, Animal Abuse, Weapons, Cybercrime)
        for category, patterns in self.harmful_categories.items():
            for pat in patterns:
                if re.search(pat, prompt_lower):
                    return InputGuardrailResult(
                        is_safe=False,
                        blocked_reason=f"Harmful / Dangerous Query Detected (Category: '{category}', Pattern: '{pat}')",
                        violation_category=category,
                        sanitized_prompt=user_prompt,
                        pii_detected=False,
                        pii_types=[]
                    )

        # Rail 3: PII Detection & Redaction
        sanitized_prompt = user_prompt
        pii_detected = False
        detected_pii_types = []

        for pii_type, (regex_pattern, replacement) in self.pii_patterns.items():
            if re.search(regex_pattern, sanitized_prompt):
                pii_detected = True
                detected_pii_types.append(pii_type)
                sanitized_prompt = re.sub(regex_pattern, replacement, sanitized_prompt)

        return InputGuardrailResult(
            is_safe=True,
            blocked_reason=None,
            violation_category=None,
            sanitized_prompt=sanitized_prompt,
            pii_detected=pii_detected,
            pii_types=detected_pii_types
        )

    # ==========================================================
    # 🔍 OUTPUT GUARDRAILS (Post-LLM Processing Interceptor)
    # ==========================================================
    def validate_output(self, llm_output: str) -> OutputGuardrailResult:
        output_lower = llm_output.lower()
        
        # Rail 1: System Secret / Key Leak Prevention
        api_key_regex = r"(AIzaSy[a-zA-Z0-9_-]{33}|eyJ[a-zA-Z0-9_-]{30,})"
        if re.search(api_key_regex, llm_output):
            sanitized_output = re.sub(api_key_regex, "[PROTECTED_API_KEY]", llm_output)
            return OutputGuardrailResult(
                is_safe=True,
                blocked_reason="Secret API Key redacted from model response",
                sanitized_output=sanitized_output
            )

        # Rail 2: Toxic Output Filter across categories
        for category, patterns in self.harmful_categories.items():
            for pat in patterns:
                if re.search(pat, output_lower):
                    return OutputGuardrailResult(
                        is_safe=False,
                        blocked_reason=f"Unsafe content detected in LLM output ({category})",
                        sanitized_output="I am sorry, but I cannot generate responses containing harmful or illegal content."
                    )

        return OutputGuardrailResult(
            is_safe=True,
            blocked_reason=None,
            sanitized_output=llm_output
        )
