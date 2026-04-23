def test_setitem_disallows_setting_created_form(self):
        mock_ctx = MagicMock()
        mock_ctx.form_ids_this_run = {"form_id"}

        with patch(
            "streamlit.runtime.scriptrunner.get_script_run_ctx", return_value=mock_ctx
        ):
            with pytest.raises(StreamlitAPIException) as e:
                self.session_state["form_id"] = "blah"
            assert "`st.session_state.form_id` cannot be modified" in str(e.value)