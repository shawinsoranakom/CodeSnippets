def test_setitem_disallows_setting_created_widget(self):
        mock_ctx = MagicMock()
        mock_ctx.widget_ids_this_run = {"widget_id"}

        with patch(
            "streamlit.runtime.scriptrunner.get_script_run_ctx", return_value=mock_ctx
        ):
            with pytest.raises(StreamlitAPIException) as e:
                self.session_state._key_id_mapping = {"widget_id": "widget_id"}
                self.session_state["widget_id"] = "blah"
            assert "`st.session_state.widget_id` cannot be modified" in str(e.value)