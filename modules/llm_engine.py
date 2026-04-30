"""
LLM Engine Module for SmartEDA
Uses Google Gemini to generate AI-powered insights, narratives, and chat responses.
"""

import google.generativeai as genai
from typing import List, Dict, Optional, Generator


# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash"  # fast and capable; user can override

SYSTEM_PROMPT_INSIGHTS = """You are SmartEDA's AI analyst — an expert data scientist who produces 
clear, insightful, and actionable Exploratory Data Analysis reports for both technical and 
non-technical audiences.

Given a dataset profile, you MUST produce a structured report with these EXACT sections:

## 🏷️ Dataset Summary
Describe the likely domain/purpose of the dataset, number of rows and columns, and overall quality.

## 🔍 Data Quality Assessment
Evaluate missing values, duplicates, data type issues, and potential data integrity problems. 
Rate overall quality: Excellent / Good / Fair / Poor with justification.

## 📊 Key Statistical Observations
Highlight the most important statistical findings: distributions, skewness, outlier-prone columns, 
notable ranges. Be specific with numbers from the profile.

## 🔗 Inter-Variable Relationships
Discuss correlations, potential causal relationships, and interesting column interactions.

## 🧹 Recommended Preprocessing Steps
List concrete steps: handle missing values (strategy per column), encoding, scaling, etc.

## 🤖 Suitable Machine Learning Models
Based on the dataset structure, recommend 3-5 ML approaches (classification/regression/clustering) 
with brief justification for each.

## ⚠️ Anomalies & Warnings
Flag anything unusual or concerning discovered in the profile.

Be specific, data-driven, and actionable. Use the exact column names and numbers from the profile."""


SYSTEM_PROMPT_CHAT = """You are SmartEDA's conversational data assistant — an expert data scientist 
helping users understand their dataset through natural language conversation.

You have access to the dataset profile and can answer questions about:
- Statistical properties of any column
- Patterns, correlations, and anomalies
- Data cleaning strategies
- Machine learning approaches
- How to interpret any metric

When code would be helpful, provide clean, executable Pandas/Python code snippets in markdown code blocks.
Keep responses concise but informative. Reference specific column names and numbers from the profile.
If you're unsure about something, say so honestly rather than guessing."""


# ─────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────

def configure_gemini(api_key: str) -> bool:
    """Configure the Gemini API with the provided key. Returns True on success."""
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return False


def generate_insights(
    profile_text: str,
    api_key: str,
    model_name: str = GEMINI_MODEL,
) -> str:
    """
    Generate a full EDA narrative insight report from the dataset profile.
    Returns the markdown-formatted report string.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT_INSIGHTS,
    )

    prompt = f"""Please analyze the following dataset profile and produce a comprehensive EDA report:

{profile_text}

Generate the full structured report as described in your instructions."""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.4,
            max_output_tokens=4096,
        ),
    )
    return response.text


def chat_with_data(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    profile_text: str,
    api_key: str,
    model_name: str = GEMINI_MODEL,
) -> str:
    """
    Multi-turn conversational interface for dataset querying.
    
    Args:
        user_message: The latest user question.
        conversation_history: List of {"role": "user"/"model", "parts": "..."} dicts.
        profile_text: Serialized dataset profile for context.
        api_key: Gemini API key.
        model_name: Gemini model to use.
    
    Returns:
        The assistant's response as a string.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT_CHAT,
    )

    # Build the full history with profile context
    profile_context = f"""DATASET PROFILE FOR REFERENCE:
{profile_text}

--- Conversation begins below ---"""

    # Convert our history format to Gemini's format
    gemini_history = []

    # Inject profile context as first user message if history is empty
    if not conversation_history:
        gemini_history = [
            {
                "role": "user",
                "parts": [profile_context],
            },
            {
                "role": "model",
                "parts": ["I've reviewed the dataset profile. I'm ready to answer your questions about this data. What would you like to know?"],
            },
        ]
    else:
        # First message pair is always the profile context
        gemini_history = [
            {
                "role": "user",
                "parts": [profile_context],
            },
            {
                "role": "model",
                "parts": ["I've reviewed the dataset profile. I'm ready to answer your questions about this data. What would you like to know?"],
            },
        ]
        # Add the rest of the conversation
        for msg in conversation_history:
            gemini_history.append({
                "role": msg["role"],
                "parts": [msg["content"]],
            })

    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(
        user_message,
        generation_config=genai.GenerationConfig(
            temperature=0.6,
            max_output_tokens=2048,
        ),
    )
    return response.text


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """
    Validate a Gemini API key by making a minimal test call.
    Returns (is_valid, message).
    """
    if not api_key or len(api_key) < 10:
        return False, "API key appears too short or empty."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        model.generate_content(
            "Say 'OK' in one word.",
            generation_config=genai.GenerationConfig(max_output_tokens=10),
        )
        return True, "API key validated successfully."
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "invalid" in err.lower():
            return False, "Invalid API key. Please check your Gemini API key."
        elif "quota" in err.lower():
            return False, "API quota exceeded. Try again later."
        else:
            return False, f"Connection error: {err}"


def list_available_models() -> List[str]:
    """Return available Gemini model names for display."""
    return [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash-thinking-exp",
    ]
