def init_session_state() -> None:
    if "api_key_submitted" not in st.session_state:
        st.session_state.api_key_submitted = False
    if "contextual_api_key" not in st.session_state:
        st.session_state.contextual_api_key = ""
    if "base_url" not in st.session_state:
        st.session_state.base_url = "https://api.contextual.ai/v1"
    if "agent_id" not in st.session_state:
        st.session_state.agent_id = ""
    if "datastore_id" not in st.session_state:
        st.session_state.datastore_id = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "processed_file" not in st.session_state:
        st.session_state.processed_file = False
    if "last_raw_response" not in st.session_state:
        st.session_state.last_raw_response = None
    if "last_user_query" not in st.session_state:
        st.session_state.last_user_query = ""