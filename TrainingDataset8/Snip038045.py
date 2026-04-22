def transparent_write(*args: Any) -> Any:
    """The function that gets magic-ified into Streamlit apps.
    This is just st.write, but returns the arguments you passed to it.
    """
    import streamlit as st

    st.write(*args)
    if len(args) == 1:
        return args[0]
    return args