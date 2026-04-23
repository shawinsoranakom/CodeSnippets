def test_duplicate_widget_id_error_when_user_key_specified(self):
        """Multiple widgets with the different generated key, but same user specified
        key should report an error.
        """

        widgets = {
            "button": lambda key=None, label="": st.button(label=label, key=key),
            "checkbox": lambda key=None, label="": st.checkbox(label=label, key=key),
            "multiselect": lambda key=None, label="": st.multiselect(
                label=label, options=[1, 2], key=key
            ),
            "radio": lambda key=None, label="": st.radio(
                label=label, options=[1, 2], key=key
            ),
            "selectbox": lambda key=None, label="": st.selectbox(
                label=label, options=[1, 2], key=key
            ),
            "slider": lambda key=None, label="": st.slider(label=label, key=key),
            "text_area": lambda key=None, label="": st.text_area(label=label, key=key),
            "text_input": lambda key=None, label="": st.text_input(
                label=label, key=key
            ),
            "time_input": lambda key=None, label="": st.time_input(
                label=label, key=key
            ),
            "date_input": lambda key=None, label="": st.date_input(
                label=label, key=key
            ),
            "number_input": lambda key=None, label="": st.number_input(
                label=label, key=key
            ),
        }

        for widget_type, create_widget in widgets.items():
            user_key = widget_type
            create_widget(label="LABEL_A", key=user_key)
            with self.assertRaises(DuplicateWidgetID) as ctx:
                # We specify different labels for widgets, so auto-generated keys
                # (widget_ids) will be different.
                # Test creating a widget with a different auto-generated key but same
                # user specified key raises an exception.
                create_widget(label="LABEL_B", key=user_key)
            self.assertEqual(
                _build_duplicate_widget_message(
                    widget_func_name=widget_type, user_key=user_key
                ),
                str(ctx.exception),
            )