def test_duplicate_widget_id_error(self):
        """Multiple widgets with the same generated key should report an error."""
        widgets = {
            "button": lambda key=None: st.button("", key=key),
            "checkbox": lambda key=None: st.checkbox("", key=key),
            "multiselect": lambda key=None: st.multiselect("", options=[1, 2], key=key),
            "radio": lambda key=None: st.radio("", options=[1, 2], key=key),
            "selectbox": lambda key=None: st.selectbox("", options=[1, 2], key=key),
            "slider": lambda key=None: st.slider("", key=key),
            "text_area": lambda key=None: st.text_area("", key=key),
            "text_input": lambda key=None: st.text_input("", key=key),
            "time_input": lambda key=None: st.time_input("", key=key),
            "date_input": lambda key=None: st.date_input("", key=key),
            "number_input": lambda key=None: st.number_input("", key=key),
        }

        for widget_type, create_widget in widgets.items():
            create_widget()
            with self.assertRaises(DuplicateWidgetID) as ctx:
                # Test creating a widget with a duplicate auto-generated key
                # raises an exception.
                create_widget()
            self.assertEqual(
                _build_duplicate_widget_message(
                    widget_func_name=widget_type, user_key=None
                ),
                str(ctx.exception),
            )

        for widget_type, create_widget in widgets.items():
            # widgets with keys are distinct from the unkeyed ones created above
            create_widget(widget_type)
            with self.assertRaises(DuplicateWidgetID) as ctx:
                # Test creating a widget with a duplicate auto-generated key
                # raises an exception.
                create_widget(widget_type)
            self.assertEqual(
                _build_duplicate_widget_message(
                    widget_func_name=widget_type, user_key=widget_type
                ),
                str(ctx.exception),
            )