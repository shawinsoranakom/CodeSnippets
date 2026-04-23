def test_transcript_disabled_error(self, mock_api_class, component_class, default_kwargs):
        """Test handling of TranscriptsDisabled error."""
        mock_api = Mock()
        mock_api.list.side_effect = TranscriptsDisabled("test123")
        mock_api_class.return_value = mock_api

        component = component_class()
        component.set_attributes(default_kwargs)

        # Test DataFrame output
        df_result = component.get_dataframe_output()
        assert isinstance(df_result, DataFrame)
        assert len(df_result) == 1
        assert "error" in df_result.columns
        assert "Failed to get YouTube transcripts" in df_result["error"][0]

        # Test Message output
        msg_result = component.get_message_output()
        assert isinstance(msg_result, Message)
        assert "Failed to get YouTube transcripts" in msg_result.text

        # Test Data output
        data_result = component.get_data_output()
        assert isinstance(data_result, Data)
        assert data_result.data["error"] is not None
        assert data_result.data["transcript"] == ""