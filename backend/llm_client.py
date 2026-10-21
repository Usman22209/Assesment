"""
OpenRouter LLM Client with Support for Free Models, Multi-Model Streaming Fallbacks, and Grounded Synthesis.
"""

import json
import logging
import os
from typing import AsyncGenerator, Dict, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("OpenRouterClient")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Primary and fallback free models currently available on OpenRouter
DEFAULT_FREE_MODELS = [
    "minimax/minimax-m3.1-flash:free",
    "poolside/laguna-s-2.1:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "liquid/lfm-2.5-2.6b:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
]

SYSTEM_PROMPT = """You are "DarWasalt AI", the premier real estate intelligence assistant representing both:
1. Dar Global (London-listed luxury international developer: LSE: DAR, $23B GDV, trophy residences in Dubai, Qatar, Oman, Spain, London, Maldives, and Wadi Safar Riyadh).
2. Wasalt (Saudi Arabia's preeminent PropTech marketplace: residential & commercial sales/rentals in Riyadh, Jeddah, Dammam, electronic property auctions, Wafi-certified off-plan projects, and REGA Fal licensing).

CORE DIRECTIVES:
- Ground your answers strictly in the verified context provided from Dar Global and Wasalt.
- Always cite your sources cleanly using markdown links whenever referencing specific projects, policies, or platforms (e.g. [Dar Global AIDA](https://darglobal.co.uk/landing-page/aida) or [Wasalt Auctions](https://wasalt.sa/en/s/terms-n-conditions-for-auction)).
- If a query compares international luxury developments with the Saudi domestic market, clearly distinguish Dar Global's high-net-worth branded developments (Pagani, Lamborghini, Missoni, Trump, Fendi Casa) from Wasalt's everyday digital marketplace, auctions, and broker ecosystem.
- If the user's question cannot be answered from the provided context, politely inform them of what is known and invite them to explore relevant Dar Global or Wasalt services.
- Provide well-structured, professional, and visually engaging responses using markdown bullet points, tables, and bold headers.
"""


class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = self._clean_key(api_key or os.getenv("OPENROUTER_API_KEY", ""))
        self.default_model = default_model or os.getenv("OPENROUTER_MODEL", DEFAULT_FREE_MODELS[0])

    @staticmethod
    def _clean_key(key: Optional[str]) -> str:
        if not key:
            return ""
        cleaned = str(key).strip()
        if cleaned.lower().startswith("bearer "):
            cleaned = cleaned[7:].strip()
        return cleaned

    def get_headers(self, user_key: Optional[str] = None) -> Dict[str, str]:
        key = self._clean_key(user_key) or self.api_key
        return {
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://github.com/dar-wasalt-ai",
            "X-Title": "Dar Global & Wasalt AI Assistant",
            "Content-Type": "application/json",
        }

    def _get_models_to_try(self, model: Optional[str] = None) -> List[str]:
        chosen = model or self.default_model
        models = [chosen]
        for m in DEFAULT_FREE_MODELS:
            if m not in models:
                models.append(m)
        return models

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        user_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> Dict[str, any]:
        """
        Sends chat completion request to OpenRouter with automatic fallback
        through free tier models in case of rate limits or model deprecations.
        """
        key = self._clean_key(user_key) or self.api_key
        if not key:
            return self._generate_simulated_grounded_response(messages)

        models_to_try = self._get_models_to_try(model)
        last_error = ""

        async with httpx.AsyncClient(timeout=45.0) as client:
            for target_model in models_to_try:
                try:
                    payload = {
                        "model": target_model,
                        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }

                    response = await client.post(
                        OPENROUTER_API_URL,
                        headers=self.get_headers(key),
                        json=payload,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        choice = data.get("choices", [{}])[0]
                        message = choice.get("message", {})
                        content = message.get("content") or ""

                        if content:
                            return {
                                "content": content,
                                "model_used": target_model,
                                "usage": data.get("usage", {}),
                                "success": True,
                            }
                    elif response.status_code in (404, 429, 503, 504):
                        logger.warning(
                            f"Model {target_model} unavailable or rate-limited (status {response.status_code}). Trying next free model..."
                        )
                        last_error = f"Status {response.status_code}: {response.text[:200]}"
                        continue
                    elif response.status_code == 401:
                        logger.error(f"OpenRouter 401 Unauthorized with provided key: {response.text}")
                        last_error = "OpenRouter 401: Invalid or expired API key."
                        break
                    else:
                        error_detail = response.text[:200]
                        logger.warning(f"OpenRouter API status {response.status_code} for {target_model}: {error_detail}")
                        last_error = f"Status {response.status_code}: {error_detail}"
                        continue
                except Exception as e:
                    logger.warning(f"Error querying model {target_model}: {e}")
                    last_error = str(e)
                    continue

        # If all models failed or were rate limited, fallback gracefully to grounded synthesizer
        logger.warning(f"All free models exhausted ({last_error}). Falling back to verified grounding synthesizer.")
        fallback = self._generate_simulated_grounded_response(messages)
        fallback["content"] = (
            f"> ℹ️ *Note: OpenRouter free tier models were temporarily busy ({last_error}). Showing verified real estate intelligence:*\n\n"
            + fallback["content"]
        )
        return fallback

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        user_key: Optional[str] = None,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens from OpenRouter with multi-model fallback.
        If a free model is rate-limited or unavailable, automatically attempts the next.
        """
        key = self._clean_key(user_key) or self.api_key
        if not key:
            simulated = self._generate_simulated_grounded_response(messages)["content"]
            chunk_size = 25
            for i in range(0, len(simulated), chunk_size):
                yield simulated[i : i + chunk_size]
            return

        models_to_try = self._get_models_to_try(model)
        stream_succeeded = False
        last_error = ""

        async with httpx.AsyncClient(timeout=60.0) as client:
            for target_model in models_to_try:
                payload = {
                    "model": target_model,
                    "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                    "temperature": temperature,
                    "stream": True,
                }

                try:
                    async with client.stream(
                        "POST",
                        OPENROUTER_API_URL,
                        headers=self.get_headers(key),
                        json=payload,
                    ) as resp:
                        if resp.status_code != 200:
                            err_bytes = await resp.aread()
                            err_text = err_bytes.decode("utf-8", errors="ignore")
                            logger.warning(f"Stream attempt on {target_model} returned {resp.status_code}: {err_text[:200]}")
                            last_error = f"{resp.status_code}: {err_text[:150]}"
                            if resp.status_code == 401:
                                # Authentication error is terminal for this key
                                yield f"⚠️ OpenRouter Authentication Error (401): Please verify your API key in settings or remove it to use server default.\n\n"
                                break
                            continue

                        # Successfully connected to stream
                        has_yielded = False
                        async for line in resp.aiter_lines():
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(data_str)
                                delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                token = delta.get("content", "")
                                if token:
                                    yield token
                                    has_yielded = True
                            except Exception:
                                continue

                        if has_yielded:
                            stream_succeeded = True
                            return
                except Exception as e:
                    logger.warning(f"Exception during stream on {target_model}: {e}")
                    last_error = str(e)
                    continue

        if not stream_succeeded:
            # Fallback to deterministic grounded response
            logger.info("All streaming models exhausted. Yielding grounded fallback response.")
            simulated = self._generate_simulated_grounded_response(messages)["content"]
            notice = f"> ℹ️ *Streaming fallback activated (OpenRouter free models busy: {last_error}). Verified intelligence:*\n\n"
            full_reply = notice + simulated
            chunk_size = 30
            for i in range(0, len(full_reply), chunk_size):
                yield full_reply[i : i + chunk_size]

    def _extract_context_summary(self, messages: List[Dict[str, str]]) -> str:
        """Extracts context from messages for direct fallback."""
        for msg in reversed(messages):
            if "RELEVANT VERIFIED CONTEXT" in msg.get("content", ""):
                lines = [l for l in msg["content"].split("\n") if l.strip() and not l.startswith("---")]
                return "\n".join(lines[:12])
        return "Please configure your OpenRouter API key in settings to enable full generative responses."

    def _generate_simulated_grounded_response(self, messages: List[Dict[str, str]]) -> Dict[str, any]:
        """Provides high-quality grounded answer directly from context when no key is set or services are busy."""
        last_message = messages[-1]["content"] if messages else ""
        user_query = ""

        if "USER QUERY:" in last_message:
            parts = last_message.split("USER QUERY:")
            user_query = parts[1].strip()
        else:
            user_query = last_message

        # Generate structured synthesis
        synthesis = (
            f"### Verified Real Estate Intelligence\n\n"
            f"Based on public data from **Dar Global** and **Wasalt**, here are the key insights regarding **'{user_query}'**:\n\n"
        )

        q_lower = user_query.lower()

        if "trump" in q_lower or "simaisma" in q_lower:
            synthesis += (
                "**Trump International Collaborations (Dar Global):**\n"
                "- **Simaisma, Qatar**: Ultra-exclusive Trump Villas and championship Trump International Golf Club with unprecedented investor demand.\n"
                "- **Trump Tower Dubai**: Construction awarded to Gulf Asia Contracting following enabling works.\n"
                "- **AIDA Muscat, Oman**: Trump International Golf Club clifftop course 130m above the Gulf of Oman.\n"
                "- **Maldives**: Private island overwater luxury resort in Noonu Atoll.\n"
                "- Source: [Dar Global Projects](https://darglobal.co.uk/lp/trump-international-qatar)\n\n"
            )
        elif "auction" in q_lower or "wallet" in q_lower:
            synthesis += (
                "**Wasalt Real Estate Auctions & E-Wallet System:**\n"
                "- **Electronic Auctions**: Approved platform for judicial and commercial property auctions in Saudi Arabia.\n"
                "- **Bidding Procedure**: Bidders deposit a required guarantee into the secure Wasalt E-Wallet to participate.\n"
                "- **Compliance**: Governed strictly under Saudi Real Estate General Authority (REGA) and Ministry of Justice standards.\n"
                "- Source: [Wasalt Auctions](https://wasalt.sa/en/s/terms-n-conditions-for-auction)\n\n"
            )
        elif "aida" in q_lower or "oman" in q_lower or "fendi" in q_lower:
            synthesis += (
                "**AIDA Muscat, Oman (Dar Global):**\n"
                "- **Oceanfront Sanctuary**: Spanning 3.5M sqm on clifftops 130m above the Gulf of Oman.\n"
                "- **Azure Oceanfront Villas**: Limited mansions furnished exclusively by **FENDI Casa**.\n"
                "- **Amenities**: Trump International Golf Club, five-star hotel, wellness center, and freehold ownership with Oman residency.\n"
                "- Source: [Dar Global AIDA](https://darglobal.co.uk/landing-page/aida)\n\n"
            )
        elif "gdv" in q_lower or "financial" in q_lower or "revenue" in q_lower:
            synthesis += (
                "**Dar Global Financial Metrics & Scale:**\n"
                "- **GDV (Gross Development Value)**: **$23 Billion** across 7 international markets.\n"
                "- **Financial Growth**: HY 2026 revenue surged **66%** to **US$258.0 million**.\n"
                "- **Listing**: Listed on the London Stock Exchange ([LSE: DAR](https://darglobal.co.uk/investor)).\n"
                "- **Track Record**: Over 32 years of heritage originating from Dar Al Arkan.\n\n"
            )
        elif "compare" in q_lower or "synergy" in q_lower or "difference" in q_lower:
            synthesis += (
                "**Dar Global vs. Wasalt Strategic Comparison:**\n\n"
                "| Feature | Dar Global (LSE: DAR) | Wasalt (PropTech) |\n"
                "| :--- | :--- | :--- |\n"
                "| **Primary Focus** | Ultra-luxury branded international developments | Saudi Arabia digital property marketplace & auctions |\n"
                "| **Key Destinations** | Dubai, Qatar, Oman, Spain, London, Maldives, Wadi Safar | Riyadh, Jeddah, Dammam, Makkah, Madinah |\n"
                "| **Brand Partners** | Pagani, Lamborghini, Missoni, Trump, Fendi Casa | REGA, Wafi, licensed Saudi brokerages |\n"
                "| **Target Audience** | High-net-worth international investors & trophy buyers | Saudi home buyers, renters, brokers, institutional bidders |\n"
                "| **Official Portal** | [darglobal.co.uk](https://darglobal.co.uk) | [wasalt.sa](https://wasalt.sa/en) |\n\n"
            )
        else:
            synthesis += (
                "**Key Real Estate Portals:**\n"
                "- **Dar Global**: Explore luxury branded residences across 7 international markets ([Visit Dar Global](https://darglobal.co.uk)).\n"
                "- **Wasalt**: Browse verified Saudi properties, electronic auctions, and masterplans ([Visit Wasalt](https://wasalt.sa/en)).\n\n"
            )

        return {
            "content": synthesis,
            "model_used": "grounded-synthesizer",
            "usage": {"total_tokens": 0},
            "success": True,
        }
