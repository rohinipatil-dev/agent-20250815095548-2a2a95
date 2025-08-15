import os
from typing import List, Dict, Tuple
import streamlit as st
from openai import OpenAI

# -----------------------------
# State Management
# -----------------------------
def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "settings" not in st.session_state:
        st.session_state.settings = default_settings()
    if "client" not in st.session_state:
        st.session_state.client = OpenAI()


def default_settings() -> Dict:
    return {
        "model": "gpt-4",
        "level": "Beginner",
        "engine": "Unity",
        "language": "C#",
        "track": "2D",
        "mode": "Tutor",
        "temperature": 0.4,
        "max_tokens": 1200,
    }


# -----------------------------
# UI Components
# -----------------------------
def render_sidebar() -> Dict:
    st.sidebar.header("Tutor Settings")
    model = st.sidebar.selectbox("Model", options=["gpt-4", "gpt-3.5-turbo"], index=0)
    level = st.sidebar.selectbox("Your Level", options=["Beginner", "Intermediate", "Advanced"], index=0)
    engine = st.sidebar.selectbox("Game Engine", options=["Unity", "Unreal", "Godot", "Pygame", "HTML5/Canvas"], index=0)
    language = st.sidebar.selectbox("Primary Language", options=["C#", "C++", "GDScript", "Python", "JavaScript"], index=0)
    track = st.sidebar.selectbox("Focus Area", options=["2D", "3D", "Mobile", "Multiplayer", "AI/Gameplay", "Audio", "UI/UX"], index=0)
    mode = st.sidebar.selectbox("Teaching Mode", options=["Tutor", "Coach", "Code Reviewer", "Curriculum Planner"], index=0)
    temperature = st.sidebar.slider("Creativity (temperature)", 0.0, 1.5, 0.4, 0.1)
    max_tokens = st.sidebar.slider("Max tokens per reply", 256, 4096, 1200, 64)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("New Chat"):
            st.session_state.messages = []
            st.toast("Started a new chat.")
    with col2:
        if st.button("Insert Starter Plan"):
            st.session_state.messages.append(
                {"role": "user", "content": "Create a 4-week learning plan for me to start making small games."}
            )
    if st.sidebar.button("Export Chat"):
        export_text = export_chat(st.session_state.messages)
        st.sidebar.download_button(
            label="Download .md",
            data=export_text,
            file_name="gamedev_tutor_chat.md",
            mime="text/markdown",
        )

    updated = {
        "model": model,
        "level": level,
        "engine": engine,
        "language": language,
        "track": track,
        "mode": mode,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }
    st.session_state.settings = updated
    return updated


def render_header():
    st.title("GameDev Mentor")
    st.caption("An AI tutor to learn game development step-by-step.")


def render_quick_starters():
    st.write("Quick starters:")
    cols = st.columns(3)
    starters = [
        "Give me a beginner roadmap for making a 2D platformer.",
        "Explain the game loop and update vs. fixed update in simple terms.",
        "Write a simple player movement script and explain each line.",
        "How do I structure a small game project folder?",
        "Help me pick the right engine for my goals.",
        "Design a small practice project for this week.",
    ]
    for i, text in enumerate(starters):
        if cols[i % 3].button(text, key=f"starter_{i}"):
            st.session_state.messages.append({"role": "user", "content": text})


# -----------------------------
# Prompt Crafting
# -----------------------------
def craft_system_prompt(settings: Dict) -> str:
    return (
        f"You are GameDev Mentor, an expert {settings['engine']} and general game development tutor. "
        f"User profile: Level={settings['level']}, Focus={settings['track']}, Preferred Language={settings['language']}. "
        f"Teaching Mode={settings['mode']}.\n\n"
        f"Goals:\n"
        f"- Teach practical game development with clear steps.\n"
        f"- Tailor examples to {settings['engine']} using {settings['language']} when applicable.\n"
        f"- Provide runnable mini-examples and bite-sized exercises.\n"
        f"- Encourage learning by building small prototypes before full games.\n"
        f"- Offer brief definitions of key terms and suggest next steps.\n\n"
        f"Guidelines:\n"
        f"- Be concise but thorough; prefer short sections and lists.\n"
        f"- When code is requested, include minimal complete snippets.\n"
        f"- If ambiguous, ask a clarifying question first.\n"
        f"- For Unity use C#; for Unreal use C++ or describe Blueprints; for Godot use GDScript; for Pygame use Python; for HTML5 use JavaScript.\n"
        f"- Include lightweight exercises and optional extensions when appropriate.\n"
        f"- Avoid proprietary or unsafe content. If a full game is requested, provide a minimal prototype and an implementation plan.\n"
        f"- Use markdown headings and code blocks for readability."
    )


def build_messages(system_prompt: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    messages = [{"role": "system", "content": system_prompt}]
    # Limit context to the last 30 turns to keep prompt size manageable
    tail = history[-60:]
    messages.extend(tail)
    return messages


# -----------------------------
# OpenAI Interaction
# -----------------------------
def generate_response(client: OpenAI, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


# -----------------------------
# Utilities
# -----------------------------
def export_chat(history: List[Dict[str, str]]) -> str:
    out = ["# GameDev Mentor Chat Export\n"]
    for msg in history:
        role = msg["role"]
        out.append(f"## {role.capitalize()}\n")
        out.append(f"{msg['content']}\n")
    return "\n".join(out)


def api_key_warning():
    if os.environ.get("OPENAI_API_KEY"):
        return
    st.warning(
        "No OpenAI API key found. Set the OPENAI_API_KEY environment variable before running this app."
    )


# -----------------------------
# Main Chat Rendering
# -----------------------------
def render_chat(settings: Dict):
    # Display conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input box
    user_input = st.chat_input("Ask about game development, request examples, or a learning plan...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    system_prompt = craft_system_prompt(settings)
                    api_messages = build_messages(system_prompt, st.session_state.messages)
                    reply = generate_response(
                        client=st.session_state.client,
                        model=settings["model"],
                        messages=api_messages,
                        temperature=settings["temperature"],
                        max_tokens=settings["max_tokens"],
                    )
                except Exception as e:
                    st.error(f"Error generating response: {e}")
                    return

                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})


# -----------------------------
# Entry Point
# -----------------------------
def main():
    st.set_page_config(page_title="GameDev Mentor", page_icon="🎮", layout="wide")
    init_state()
    api_key_warning()
    settings = render_sidebar()
    render_header()

    if not st.session_state.messages:
        st.info("Tell me your goals (e.g., 'I want to make a 2D platformer in Unity using C#').")
        render_quick_starters()

    render_chat(settings)


if __name__ == "__main__":
    main()