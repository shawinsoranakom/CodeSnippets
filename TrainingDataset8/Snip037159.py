def set_multiselect_9_to_have_bad_state():
    if "multiselect 9" in st.session_state:
        st.session_state["multiselect 9"] = ["male", "female"]