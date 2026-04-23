def test_set_widget_attrs_nonexistent(self):
        session_state = SessionState()
        session_state._set_widget_metadata(create_metadata("fake_widget_id", ""))

        self.assertIsInstance(
            session_state._new_widget_state.widget_metadata["fake_widget_id"],
            WidgetMetadata,
        )