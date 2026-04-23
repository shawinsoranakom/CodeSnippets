def _show_beta_warning(name: str, date: str) -> None:
    streamlit.warning(
        f"Please replace `st.beta_{name}` with `st.{name}`.\n\n"
        f"`st.beta_{name}` will be removed after {date}."
    )