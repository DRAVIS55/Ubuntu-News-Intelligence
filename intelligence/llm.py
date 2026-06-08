"""
intelligence/llm.py — LLM abstraction layer
Supports: Anthropic (Claude), OpenAI, local llama.cpp
Swap providers by changing LLM_PROVIDER in .env

This module is framework-agnostic and works identically under Django.
"""

import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM interface. All intelligence modules use this class
    so that switching providers requires zero code changes.
    """

    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self._client = None
        self._local_llm = None
        self._init_client()

    def _init_client(self):
        if self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            logger.info(f"LLM: Anthropic ({config.ANTHROPIC_MODEL})")

        elif self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=config.OPENAI_API_KEY)
            logger.info(f"LLM: OpenAI ({config.OPENAI_MODEL})")

        elif self.provider == "local":
            try:
                from llama_cpp import Llama
                self._local_llm = Llama(
                    model_path=config.LOCAL_MODEL_PATH,
                    n_ctx=config.LOCAL_MODEL_N_CTX,
                    n_gpu_layers=config.LOCAL_MODEL_N_GPU_LAYERS,
                    verbose=False,
                )
                logger.info(f"LLM: Local model ({config.LOCAL_MODEL_PATH})")
            except ImportError:
                logger.error(
                    "llama-cpp-python not installed. "
                    "Run: pip install llama-cpp-python"
                )
                raise
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {self.provider}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> str:
        """
        Generate a completion. Returns the text response.

        Args:
            prompt: The user message / instruction
            system: Optional system prompt (persona / context)
            max_tokens: Maximum tokens in the response
            temperature: 0.0 = deterministic, 1.0 = creative
        """
        if not system:
            system = (
                "You are an expert African news analyst with deep knowledge of "
                "East African politics, economics, and regional dynamics. "
                "You provide accurate, factual analysis grounded in evidence. "
                "You understand Kenyan, Tanzanian, Ugandan, and Ethiopian contexts. "
                "Always cite the sources provided to you. Never speculate beyond the evidence."
            )

        try:
            if self.provider == "anthropic":
                return self._complete_anthropic(prompt, system, max_tokens, temperature)
            elif self.provider == "openai":
                return self._complete_openai(prompt, system, max_tokens, temperature)
            elif self.provider == "local":
                return self._complete_local(prompt, system, max_tokens, temperature)
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise

    def _complete_anthropic(self, prompt, system, max_tokens, temperature):
        response = self._client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _complete_openai(self, prompt, system, max_tokens, temperature):
        response = self._client.chat.completions.create(
            model=config.OPENAI_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    def _complete_local(self, prompt, system, max_tokens, temperature):
        full_prompt = f"[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{prompt} [/INST]"
        output = self._local_llm(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["[INST]", "</s>"],
        )
        return output["choices"][0]["text"].strip()


# ── Singleton ───────────────────────────────────────────────────────────────────
_llm_instance: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """Return the shared LLM client (initialised once)."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance
