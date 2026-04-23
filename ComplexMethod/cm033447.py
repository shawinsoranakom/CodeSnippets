def test_progress_default_values(self):
        """Test default values."""
        progress = MigrationProgress(
            es_index="test_index",
            ob_table="test_table",
        )

        assert progress.failed_documents == 0
        assert progress.last_sort_values == []
        assert progress.last_batch_ids == []
        assert progress.error_message == ""
        assert progress.schema_converted is False
        assert progress.table_created is False
        assert progress.indexes_created is False