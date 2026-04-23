def is_in_form(dg: "streamlit.delta_generator.DeltaGenerator") -> bool:
    """True if the DeltaGenerator is inside an st.form block."""
    return current_form_id(dg) != ""