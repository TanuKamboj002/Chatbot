"""
chat_core.py — Core Chat Engine with memory and modes

Features:
- Per-session chat history (in-memory buffer with auto-trimming)
- Modes: "chat", "code", "knowledge"
- Uses OpenAI Chat Completions API (via openai>=1.0 Python SDK)
- Optional Wikipedia enrichment in knowledge mode
- Clean API for integration into app.py

Requirements (see requirements.txt):
- openai
- wikipedia (used in knowledge.py)

Environment:
- Set OPENAI_API_KEY in your environment
- Optionally set OPENAI_MODEL (default: gpt-4o-mini)

Example Usage:
    from chat_core import ChatEngine
    ce = ChatEngine()
    reply = ce.respond("Hello!", mode="chat")
    print(reply)
"""

from __future__ import annotations
import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# --------------------------- Optional Imports ---------------------------
try:
    from openai import OpenAI  # OpenAI SDK v1.x
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

try:
    from knowledge import get_summary as wiki_summary  # lightweight import
    _HAS_WIKI = True
except Exception:
    _HAS_WIKI = False

# --------------------------- Logging -----------------------------------
LOGGER = logging.getLogger("chat_core")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

# --------------------------- System Prompts -----------------------------
DEFAULT_SYSTEM_PROMPTS: Dict[str, str] = {
    "chat": (
        "You are a friendly, concise AI assistant. Be helpful, honest, and "
        "avoid verbosity. Use simple language unless asked for detail."
    ),
    "code": (
        "You are a senior software engineer. Provide precise, secure, and "
        "production-ready answers. Show minimal runnable examples. "
        "Mention time/space complexity when relevant."
    ),
    "knowledge": (
        "You are a factual knowledge assistant. When provided with external "
        "context (e.g., from Wikipedia), cite it naturally and separate facts "
        "from speculation. If uncertain, say so."
    ),
}

# Safe default model; override via environment or constructor
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --------------------------- Chat Engine -------------------------------
@dataclass
class ChatEngine:
    """Lightweight chat engine with mode-aware responses and memory."""

    model: str = DEFAULT_MODEL
    memory_size: int = 40
    system_prompts: Dict[str, str] = field(default_factory=lambda: DEFAULT_SYSTEM_PROMPTS.copy())
    enable_wiki_in_knowledge_mode: bool = True

    # Internal state
    _messages: List[Dict[str, str]] = field(default_factory=list, init=False)
    _client: Optional["OpenAI"] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if _HAS_OPENAI:
            try:
                self._client = OpenAI()
                LOGGER.info("OpenAI client initialized with model '%s'", self.model)
            except Exception as e:
                LOGGER.warning("Failed to initialize OpenAI client: %s", e)
        else:
            LOGGER.warning("openai package not available — ChatEngine will not call API.")

    # ----------------------- Public API -------------------------------
    def reset(self) -> None:
        """Clear chat history."""
        self._messages.clear()
        LOGGER.info("Chat history reset.")

    def get_history(self) -> List[Dict[str, str]]:
        """Return current chat history."""
        return list(self._messages)

    def set_system_prompt(self, mode: str, prompt: str) -> None:
        """Set or override system prompt for a given mode."""
        self.system_prompts[mode] = prompt
        LOGGER.info("System prompt updated for mode '%s'", mode)

    def respond(self, user_input: str, mode: str = "chat") -> str:
        """Generate a reply for given user input and mode."""
        mode_key = self._normalize_mode(mode)
        system_prompt = self.system_prompts.get(mode_key, DEFAULT_SYSTEM_PROMPTS["chat"])

        # Save user message
        self._append_message({"role": "user", "content": user_input})

        # Optional: Wikipedia enrichment
        tool_context = None
        if mode_key == "knowledge" and self.enable_wiki_in_knowledge_mode and _HAS_WIKI:
            try:
                summary = wiki_summary(user_input, sentences=4)
                if summary.strip():
                    tool_context = f"\n[External Source: Wikipedia]\n{summary.strip()}\n[End Source]\n"
                    LOGGER.info("Wikipedia context attached (%d chars)", len(tool_context))
            except Exception as e:
                LOGGER.warning("Wikipedia enrichment failed: %s", e)

        # Build final messages
        messages = self._build_model_messages(system_prompt, tool_context)

        # Call model
        reply_text = self._call_llm(messages)

        # Save assistant reply
        self._append_message({"role": "assistant", "content": reply_text})
        return reply_text

    # ----------------------- Internal Helpers -------------------------
    def _normalize_mode(self, mode: str) -> str:
        m = (mode or "").strip().lower()
        if m in {"chat"}:
            return "chat"
        if m in {"code", "code helper", "programming"}:
            return "code"
        if m in {"knowledge", "facts", "knowledge assistant"}:
            return "knowledge"
        return "chat"

    def _append_message(self, msg: Dict[str, str]) -> None:
        """Append message to history with memory trimming."""
        self._messages.append(msg)
        overflow = max(0, len(self._messages) - self.memory_size)
        if overflow:
            del self._messages[:overflow]
            LOGGER.debug("Trimmed history by %d messages", overflow)

    def _build_model_messages(self, system_prompt: str, tool_context: Optional[str]) -> List[Dict[str, str]]:
        msgs: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if tool_context:
            msgs.append({
                "role": "system",
                "content": (
                    "Use the following external context to answer. Cite it naturally "
                    "when used.\n" + tool_context
                ),
            })
        msgs.extend(self._messages[-(self.memory_size - len(msgs)):])
        return msgs

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API or return fallback response."""
        if not _HAS_OPENAI or self._client is None:
            LOGGER.error("OpenAI SDK unavailable — returning local fallback.")
            return self._local_stub(messages)

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            LOGGER.error("OpenAI API error: %s", e)
            return self._local_stub(messages)

    def _local_stub(self, messages: List[Dict[str, str]]) -> str:
        """Fallback if OpenAI is unavailable."""
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"[Local fallback] I can't reach the model. Echo: {last_user[:400]}"

# --------------------------- Module Test ------------------------------
if __name__ == "__main__":
    ce = ChatEngine()
    print("Mode: chat ->", ce.respond("Give me two productivity tips.", mode="chat"))
    print("Mode: code ->", ce.respond("How do I reverse a linked list in Python?", mode="code"))
    print("Mode: knowledge ->", ce.respond("What is the Taj Mahal?", mode="knowledge"))

if __name__ == "__main__":
    ce = ChatEngine()
    while True:
        msg = input("You: ")
        if msg.lower() in {"exit", "quit"}:
            break
        response = ce.respond(msg, mode="chat")  # or "code" / "knowledge"
        print("Bot:", response)

if __name__ == "__main__":
    ce = ChatEngine()

    print("Chatbot is running! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # You can choose mode here: "chat", "code", "knowledge"
        mode = input("Select mode (chat/code/knowledge): ").strip().lower()
        if mode not in {"chat", "code", "knowledge"}:
            mode = "chat"

        response = ce.respond(user_input, mode=mode)
        print("Bot:", response)
