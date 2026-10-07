"""Sublab Easy - a course-registration chatbot, and the bill it runs up.

Two lessons live in this file, and neither is the chatbot.

The first is that OpenRouter speaks the OpenAI wire format, so the *same client
library* reaches both providers. Look at how little differs between the two
client functions below.

The second is what a "conversation" actually is. The model remembers nothing.
Every turn you resend the entire history, so the input token count climbs on
every turn while your questions stay the same length. You are going to watch
that happen and put the numbers in a table. Week 4 is about what to do once
that becomes a problem.

Fill in every `TODO`. Keep the function signatures - the other sublabs import
from this file, and the examples in the docstrings say what each one must
return.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

CATALOGUE = Path(__file__).resolve().parent.parent / "data" / "courses.json"

# List price in USD per MILLION tokens, retrieved 2026-08-19. These drift.
# Re-check before you quote them anywhere that matters.
RATES_PER_MTOK = {
    # OpenAI, called directly
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-5.6-sol": (5.00, 30.00),
    # Reached through OpenRouter
    "google/gemma-4-26b-a4b-it:free": (0.00, 0.00),
    "meta-llama/llama-3.1-8b-instruct:free": (0.00, 0.00),
    "mistralai/mistral-7b-instruct:free": (0.00, 0.00),
    "qwen/qwen3.8-27b": (0.45, 3.20),
    "deepseek/deepseek-v4-flash-0731": (0.14, 0.28),
}


def load_catalogue() -> dict:
    """The course catalogue, the registration rules, and the student."""
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Reaching the two providers
# --------------------------------------------------------------------------

def openai_client() -> OpenAI:
    """A client pointed at OpenAI itself."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env.")
    return OpenAI(api_key=key)


def openrouter_client() -> OpenAI:
    """A client pointed at OpenRouter.

    Same class, same methods. Note what you had to change - the written
    question at the end of this sublab asks you exactly that.
    """
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Copy .env.example to .env.")
    return OpenAI(
        api_key=key,
        base_url=OPENROUTER_BASE_URL
    )


def client_for(via: str) -> OpenAI:
    """Given. `via` is "openai" or "openrouter"."""
    if via == "openai":
        return openai_client()
    if via == "openrouter":
        return openrouter_client()
    raise ValueError('via must be "openai" or "openrouter", got ' + repr(via))


# --------------------------------------------------------------------------
# The bot's instructions
# --------------------------------------------------------------------------

def build_system_prompt(catalogue: dict) -> str:
    catalogue_text = json.dumps(catalogue, indent=2, ensure_ascii=False)

    return f"""You are a strict university course registration advisor.

Here is the complete database of courses, university rules, and the current student's record:
{catalogue_text}

STRICT REGISTRATION INSTRUCTIONS:
1. Check prerequisites: the student must have completed all prerequisites for a course.
2. Check schedules: ensure there are no meeting time collisions between chosen courses.
3. Check availability: the requested course must have seats > 0.
4. Check limits: the total credits cannot exceed the student's credit limit.
5. CRITICAL REFUSAL RULE: You must absolutely refuse to register the student for any course code not explicitly listed in the database above. Do not invent, hallucinate, or create new courses, credits, rooms, or instructors. If it is not in the JSON, say it does not exist."""


# --------------------------------------------------------------------------
# One turn
# --------------------------------------------------------------------------

def chat(messages: list[dict], model: str = "gpt-5.6-luna",
         via: str = "openai") -> dict:
    client = client_for(via)
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    return {
        "text": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "model": model
    }


def ask_once(prompt: str, model: str = "gpt-5.6-luna",
             via: str = "openai") -> dict:
    """Given. A one-shot call is just a conversation one message long."""
    return chat([{"role": "user", "content": prompt}], model=model, via=via)


# --------------------------------------------------------------------------
# The conversation
# --------------------------------------------------------------------------

def new_conversation(catalogue: dict) -> list[dict]:
    """Given. A fresh history holding only the system message."""
    return [{"role": "system", "content": build_system_prompt(catalogue)}]


def run_turn(history: list[dict], user_text: str, model: str = "gpt-5.6-luna",
             via: str = "openai") -> tuple[list[dict], dict]:
    """Given. One turn: append the user's message, send EVERYTHING, append the
    reply.

    Read this function rather than skimming it. The list only ever grows, and
    all of it goes over the wire on every call. That is where your input token
    count is coming from.

    Returns:
        (the new history, the usage dict from `chat`)
    """
    history = history + [{"role": "user", "content": user_text}]
    reply = chat(history, model=model, via=via)
    history = history + [{"role": "assistant", "content": reply["text"]}]
    return history, reply


# --------------------------------------------------------------------------
# The bill
# --------------------------------------------------------------------------

def estimate_cost(input_tokens: int, output_tokens: int,
                  rate_in: float, rate_out: float) -> float:
    """Dollar cost of one call."""
    return (input_tokens * rate_in / 1_000_000) + (output_tokens * rate_out / 1_000_000)


def cost_of(usage: dict) -> float:
    """Given. Cost of one result dict from `chat`."""
    rate_in, rate_out = RATES_PER_MTOK[usage["model"]]
    return estimate_cost(usage["input_tokens"], usage["output_tokens"],
                         rate_in, rate_out)


def conversation_cost(usages: list[dict]) -> float:
    """What the whole conversation cost: the sum of every turn."""
    return sum(cost_of(u) for u in usages)


# --------------------------------------------------------------------------
# The five turns you must run. Do not edit turns 1-4; they are what makes every
# submission comparable. Turn 5 is turn 1 again, in Kazakh or Russian - write
# it yourself, and notice what it costs. Sublab Harder explains why.
# --------------------------------------------------------------------------

SCRIPT = [
    "I am a third-year student. Which courses am I still eligible to register for?",
    "Register me for CSS-4007 and CSS-4102.",
    "How many credits would that be in total, and am I within the limit?",
    "Add CSS-4090 Quantum Machine Learning to my schedule.",
    "Я студент третьего курса. На какие предметы я еще могу зарегистрироваться?",
]


def run_script(model: str, via: str) -> list[dict]:
    """Given. Run the five scripted turns and print the running bill."""
    history = new_conversation(load_catalogue())
    usages = []

    print("\n===== " + via + " / " + model + " =====")
    for i, user_text in enumerate(SCRIPT, start=1):
        history, usage = run_turn(history, user_text, model=model, via=via)
        usages.append(usage)
        print("\n--- turn %d ---" % i)
        print("you: " + user_text)
        print("bot: " + usage["text"])
        print("     in=%6d  out=%5d  $%.6f"
              % (usage["input_tokens"], usage["output_tokens"], cost_of(usage)))

    print("\n%10s%8s%7s%12s" % ("", "in", "out", "cost"))
    for i, u in enumerate(usages, start=1):
        print("turn %-5d%8d%7d%12.6f"
              % (i, u["input_tokens"], u["output_tokens"], cost_of(u)))
    print("%25s%s" % ("", "-" * 12))
    print("%25s%12.6f" % ("total", conversation_cost(usages)))
    return usages


if __name__ == "__main__":
    if any(t.startswith("TODO") for t in SCRIPT):
        raise SystemExit("Write turn 5 in Kazakh or Russian first.")

    #Work, all good. run_script("gpt-5.6-luna", "openai")
    #Doesn't work? (429 err) run_script("google/gemma-4-26b-a4b-it:free", "openrouter")
    #Doesn't work too, because not free anymore (404 err) run_script("meta-llama/llama-3.1-8b-instruct:free", "openrouter")
    # 404 too run_script("mistralai/mistral-7b-instruct:free", "openrouter" )