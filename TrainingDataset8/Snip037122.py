def on_checkbox_change(changed_checkbox_number):
        if changed_checkbox_number == 1:
            st.session_state.checkbox2 = False
        elif changed_checkbox_number == 2:
            st.session_state.checkbox1 = False