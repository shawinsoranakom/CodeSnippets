def on_click(x, y):
        if "click_count" not in st.session_state:
            st.session_state.click_count = 0

        st.session_state.click_count += 1
        st.session_state.x = x
        st.session_state.y = y