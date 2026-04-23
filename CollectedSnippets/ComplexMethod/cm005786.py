def test_get_metadata_fast_recounts_stale_zero_chunk_metadata(
        self, mock_update_metrics, mock_get_directory_size, mock_kb_path
    ):
        metadata_file = mock_kb_path / "embedding_metadata.json"
        sample_meta = {
            "chunks": 0,
            "words": 0,
            "characters": 0,
            "avg_chunk_size": 0.0,
            "embedding_provider": "OpenAI",
            "embedding_model": "text-embedding-3-small",
            "id": "test-uuid",
            "size": 128,
            "source_types": [],
            "chunk_size": None,
            "chunk_overlap": None,
            "separator": None,
        }
        metadata_file.write_text(json.dumps(sample_meta))
        (mock_kb_path / "chroma.sqlite3").write_text("")
        mock_get_directory_size.return_value = 4096

        def populate_metrics(_kb_path, metadata):
            metadata.update({"chunks": 2, "words": 3, "characters": 14, "avg_chunk_size": 7.0})

        mock_update_metrics.side_effect = populate_metrics

        result = KBAnalysisHelper.get_metadata(mock_kb_path, fast=True)
        stored_metadata = json.loads(metadata_file.read_text())

        assert result["chunks"] == 2
        assert result["words"] == 3
        assert result["characters"] == 14
        assert result["avg_chunk_size"] == 7.0
        assert result["size"] == 4096
        assert stored_metadata["chunks"] == 2
        assert stored_metadata["size"] == 4096
        mock_update_metrics.assert_called_once()
        mock_get_directory_size.assert_called_once_with(mock_kb_path)