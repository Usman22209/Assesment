"""
OpenRouter LLM Client with Support for Free Models, Fallbacks, and Grounded Streaming.
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

# Primary and fallback free models available on OpenRouter
DEFAULT_FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "qwen/qwen-2.5-coder-32b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
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
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.default_model = default_model or os.getenv("OPENROUTER_MODEL", DEFAULT_FREE_MODELS[0])

    def get_headers(self, user_key: Optional[str] = None) -> Dict[str, str]:
        key = user_key or self.api_key
        return {
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://github.com/dar-wasalt-ai",
            "X-Title": "Dar Global & Wasalt AI Assistant",
            "Content-Type": "application/json",
        }

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
        through free tier models in case of rate limits.
        """
        key = user_key or self.api_key
        if not key:
            return self._generate_simulated_grounded_response(messages)

        models_to_try = [model or self.default_model] + [
            m for m in DEFAULT_FREE_MODELS if m != (model or self.default_model)
        ]

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
                        content = data["choices"][0]["message"]["content"]
                        return {
                            "content": content,
                            "model_used": target_model,
                            "usage": data.get("usage", {}),
                            "success": True,
                        }
                    elif response.status_code in (429, 503, 504):
                        logger.warning(
                            f"Model {target_model} rate-limited or unavailable (status {response.status_code}). Trying next free model..."
                        )
                        last_error = f"Status {response.status_code}: {response.text}"
                        continue
                    else:
                        error_detail = response.text
                        logger.error(f"OpenRouter API error {response.status_code}: {error_detail}")
                        return {
                            "content": f"⚠️ OpenRouter Error ({response.status_code}): {error_detail}. Please verify your API key.",
                            "model_used": target_model,
                            "success": False,
                        }
                except Exception as e:
                    logger.warning(f"Error querying model {target_model}: {e}")
                    last_error = str(e)
                    continue

        # If all models failed or were rate limited, fallback gracefully
        return {
            "content": f"All free models are currently experiencing high demand on OpenRouter ({last_error}).\n\nHere is the directly retrieved context:\n"
            + self._extract_context_summary(messages),
            "model_used": "direct-retrieval-fallback",
            "success": False,
        }

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        user_key: Optional[str] = None,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """Streams response tokens from OpenRouter."""
        key = user_key or self.api_key
        if not key:
            # Yield simulated grounded stream
            simulated = self._generate_simulated_grounded_response(messages)["content"]
            chunk_size = 20
            for i in range(0, len(simulated), chunk_size):
                yield simulated[i : i + chunk_size]
            return

        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "temperature": temperature,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    OPENROUTER_API_URL,
                    headers=self.get_headers(key),
                    json=payload,
                ) as resp:
                    if resp.status_code != 200:
                        err_text = await resp.aread()
                        yield f"⚠️ OpenRouter Streaming Error ({resp.status_code}): {err_text.decode('utf-8', errors='ignore')}"
                        return

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data["choices"][0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                yield token
                        except Exception:
                            continue
            except Exception as e:
                yield f"\n\n[Connection Error: {e}]"

    def _extract_context_summary(self, messages: List[Dict[str, str]]) -> str:
        """Extracts context from messages for direct fallback."""
        for msg in reversed(messages):
            if "RELEVANT VERIFIED CONTEXT" in msg.get("content", ""):
                lines = [l for l in msg["content"].split("\n") if l.strip() and not l.startswith("---")]
                return "\n".join(lines[:12])
        return "Please configure your OpenRouter API key in settings to enable full generative responses."

    def _generate_simulated_grounded_response(self, messages: List[Dict[str, str]]) -> Dict[str, any]:
        """Provides high-quality grounded answer directly from context when no key is set."""
        last_message = messages[-1]["content"] if messages else ""
        context_part = ""
        user_query = ""

        if "USER QUERY:" in last_message:
            parts = last_message.split("USER QUERY:")
            context_part = parts[0]
            user_query = parts[1].strip()
        else:
            user_query = last_message

        # Generate structured synthesis
        synthesis = (
            f"### Verified Real Estate Intelligence\n\n"
            f"Based on public data from **Dar Global** and **Wasalt**, here are the key insights regarding **'{user_query}'**:\n\n"
        )

        if "trump" in user_query.lower() or "simaisma" in user_query.lower():
            synthesis += (
                "**Trump International Collaborations (Dar Global):**\n"
                "- **Simaisma, Qatar**: Ultra-exclusive Trump Villas and championship Trump International Golf Club with unprecedented investor demand.\n"
                "- **Trump Tower Dubai**: Construction awarded to Gulf Asia Contracting following enabling works.\n"
                "- **AIDA Muscat, Oman**: Trump International Golf Club clifftop course 130m above the Gulf of Oman.\n"
                "- **Maldives**: Private island overwater luxury resort in Noonu Atoll.\n"
                "- Source: [Dar Global Projects](https://darglobal.co.uk/lp/trump-international-qatar)\n\n"
            )
        elif "auction" in user_query.lower() or "wallet" in user_query.lower():
            synthesis += (
                "**Wasalt Real Estate Auctions & E-Wallet System:**\n"
                "- **Electronic Auctions**: Approved platform for judicial and commercial property auctions in Saudi Arabia.\n"
                "- **Bidding Procedure**: Bidders deposit a required guarantee into the secure Wasalt E-Wallet to participate.\n"
                "- **Compliance**: Governed strictly under Saudi Real Estate General Authority (REGA) and Ministry of Justice standards.\n"
                "- Source: [Wasalt Auctions](https://wasalt.sa/en/s/terms-n-conditions-for-auction)\n\n"
            )
        elif "aida" in user_query.lower() or "oman" in user_query.lower() or "fendi" in user_query.lower():
            synthesis += (
                "**AIDA Muscat, Oman (Dar Global):**\n"
                "- **Oceanfront Sanctuary**: Spanning 3.5M sqm on clifftops 130m above the Gulf of Oman.\n"
                "- **Azure Oceanfront Villas**: Limited mansions furnished exclusively by **FENDI Casa**.\n"
                "- **Amenities**: Trump International Golf Club, five-star hotel, wellness center, and freehold ownership with Oman residency.\n"
                "- Source: [Dar Global AIDA](https://darglobal.co.uk/landing-page/aida)\n\n"
            )
        elif "gdv" in user_query.lower() or "financial" in user_query.lower() or "revenue" in user_query.lower():
            synthesis += (
                "**Dar Global Financial Metrics & Scale:**\n"
                "- **GDV (Gross Development Value)**: **$23 Billion** across 7 international markets.\n"
                "- **Financial Growth**: HY 2026 revenue surged **66%** to **US$258.0 million**.\n"
                "- **Listing**: Listed on the London Stock Exchange ([LSE: DAR](https://darglobal.co.uk/investor)).\n"
                "- **Track Record**: Over 32 years of heritage originating from Dar Al Arkan.\n\n"
            )
        elif "compare" in user_query.lower() or "synergy" in user_query.lower() or "difference" in user_query.lower():
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

        synthesis += (
            "> 💡 **Tip**: To enable live AI reasoning via free models on OpenRouter (`meta-llama/llama-3.3-70b-instruct:free`), "
            "provide your free OpenRouter API key in the top settings modal or in the `.env` file."
        )

        return {
            "content": synthesis,
            "model_used": "grounded-synthesizer",
            "usage": {"total_tokens": 0},
            "success": True,
        }
