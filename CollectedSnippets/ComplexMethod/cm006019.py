def test_split_text_with_metadata(self):
        """Test text splitting while preserving metadata."""
        component = SplitTextComponent()
        test_metadata = {"source": "test.txt", "author": "test"}
        test_text = "First chunk\nSecond chunk"
        component.set_attributes(
            {
                "data_inputs": [Data(text=test_text, data=test_metadata)],
                "chunk_overlap": 0,
                "chunk_size": 7,
                "separator": "\n",
                "clean_output": False,
                "session_id": "test_session",
                "sender": "test_sender",
                "sender_name": "test_sender_name",
            }
        )

        data_frame = component.split_text()
        assert isinstance(data_frame, DataFrame), "Expected DataFrame instance"
        assert len(data_frame) == 2, f"Expected DataFrame with 2 rows, got {len(data_frame)}"
        assert "First chunk" in data_frame.iloc[0]["text"], (
            f"Expected 'First chunk', got '{data_frame.iloc[0]['text']}'"
        )
        assert "Second chunk" in data_frame.iloc[1]["text"], (
            f"Expected 'Second chunk', got '{data_frame.iloc[1]['text']}'"
        )
        # Loop over each row to check metadata
        for _, row in data_frame.iterrows():
            assert row["source"] == test_metadata["source"], (
                f"Expected source '{test_metadata['source']}', got '{row['source']}'"
            )
            assert row["author"] == test_metadata["author"], (
                f"Expected author '{test_metadata['author']}', got '{row['author']}'"
            )