import streamlit as st
import uuid
import requests

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------
DEFAULT_SERVER_URL = "http://127.0.0.1:8000"
DEFAULT_APP_NAME = "my_agent"
USER_ID = "streamlit-user"

# ---------------------------------------------------
# Page Config
# ---------------------------------------------------
st.set_page_config(
    page_title="Content Intelligence System",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Content Intelligence System")
st.markdown(
    "From your oldest uploads to today's newest release—"
    "get instant answers from your entire YouTube catalog."
)

# ---------------------------------------------------
# Session State
# ---------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "adk_session_id" not in st.session_state:
    st.session_state.adk_session_id = (
        f"session-{uuid.uuid4().hex[:12]}"
    )

if "session_initialized" not in st.session_state:
    st.session_state.session_initialized = False

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------
with st.sidebar:

    st.header("ADK Connection Details")

    ADK_SERVER_URL = st.text_input(
        "Server URL",
        value=DEFAULT_SERVER_URL
    )

    ADK_APP_NAME = st.text_input(
        "App Name",
        value=DEFAULT_APP_NAME
    )

    st.markdown("---")

    st.caption(
        f"Active Session ID: "
        f"`{st.session_state.adk_session_id}`"
    )

    if st.button(
        "Clear Chat / Reset Context",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.adk_session_id = (
            f"session-{uuid.uuid4().hex[:12]}"
        )

        st.session_state.session_initialized = False

        st.rerun()

# ---------------------------------------------------
# Create ADK Session
# ---------------------------------------------------
def create_adk_session():

    session_endpoint = (
        f"{ADK_SERVER_URL.rstrip('/')}"
        f"/apps/{ADK_APP_NAME}"
        f"/users/{USER_ID}"
        f"/sessions/{st.session_state.adk_session_id}"
    )

    response = requests.post(
        session_endpoint,
        json={},
        timeout=30
    )

    response.raise_for_status()

    st.session_state.session_initialized = True


# ---------------------------------------------------
# Display Chat History
# ---------------------------------------------------
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------
# Chat Input
# ---------------------------------------------------
if prompt := st.chat_input("Ask me anything..."):

    # -----------------------------------------------
    # Show User Message
    # -----------------------------------------------
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # -----------------------------------------------
    # Assistant Response
    # -----------------------------------------------
    with st.chat_message("assistant"):

        with st.spinner("Searching YouTube catalog..."):

            try:

                # -----------------------------------
                # Initialize Session Once
                # -----------------------------------
                if not st.session_state.session_initialized:
                    create_adk_session()

                # -----------------------------------
                # Run Endpoint
                # -----------------------------------
                run_endpoint = (
                    f"{ADK_SERVER_URL.rstrip('/')}/run"
                )

                payload = {
                    "appName": ADK_APP_NAME,
                    "userId": USER_ID,
                    "sessionId": st.session_state.adk_session_id,
                    "newMessage": {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                }

                response = requests.post(
                    run_endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/json"
                    },
                    timeout=60
                )

                response.raise_for_status()

                # -----------------------------------
                # Parse Response
                # -----------------------------------
                events = response.json()

                # DEBUG VIEW
                with st.expander("🔍 Raw ADK Response"):
                    st.json(events)

                agent_reply = None

                if isinstance(events, list):

                    for event in reversed(events):

                        # -------------------------
                        # FORMAT 1
                        # event["message"]
                        # -------------------------
                        if "message" in event:

                            message = event["message"]

                            parts = message.get(
                                "parts",
                                []
                            )

                            for part in parts:

                                if (
                                    isinstance(part, dict)
                                    and "text" in part
                                ):

                                    agent_reply = part["text"]
                                    break

                        # -------------------------
                        # FORMAT 2
                        # event["content"]
                        # -------------------------
                        elif "content" in event:

                            content = event["content"]

                            parts = content.get(
                                "parts",
                                []
                            )

                            for part in parts:

                                if (
                                    isinstance(part, dict)
                                    and "text" in part
                                ):

                                    agent_reply = part["text"]
                                    break

                        # -------------------------
                        # FORMAT 3
                        # event["parts"]
                        # -------------------------
                        elif "parts" in event:

                            for part in event["parts"]:

                                if (
                                    isinstance(part, dict)
                                    and "text" in part
                                ):

                                    agent_reply = part["text"]
                                    break

                        # -------------------------
                        # Stop if found
                        # -------------------------
                        if agent_reply:
                            break

                # -----------------------------------
                # Fallback
                # -----------------------------------
                if not agent_reply:
                    agent_reply = (
                        "No response generated."
                    )

                # -----------------------------------
                # Show Response
                # -----------------------------------
                st.markdown(agent_reply)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": agent_reply
                })

            except requests.exceptions.ConnectionError:

                st.error(
                    "⚠️ Connection Error: "
                    "Could not connect to ADK server."
                )

            except requests.exceptions.HTTPError as e:

                st.error(
                    f"⚠️ API Error: "
                    f"{e.response.status_code}"
                )

                try:
                    st.json(e.response.json())
                except:
                    st.text(e.response.text)

            except Exception as e:

                st.error(
                    f"⚠️ Unexpected Error: {str(e)}"
                )