def test_get_dataframe_output_success(
        self, mock_api_class, component_class, default_kwargs, mock_transcript_data, mock_transcript_list
    ):
        """Test successful DataFrame output generation."""
        mock_api = Mock()
        mock_api.list.return_value = mock_transcript_list
        mock_api.fetch.return_value = mock_transcript_data
        mock_api_class.return_value = mock_api

        component = component_class()
        component.set_attributes(default_kwargs)
        result = component.get_dataframe_output()

        assert isinstance(result, DataFrame)
        result_df = result
        assert len(result_df) == 2  # Two chunks (0-60s and 60-90s)
        assert list(result_df.columns) == ["timestamp", "text"]
        assert result_df.iloc[0]["timestamp"] == "00:00"
        assert result_df.iloc[1]["timestamp"] == "01:00"
        assert "First part" in result_df.iloc[0]["text"]
        assert "Third part" in result_df.iloc[1]["text"]