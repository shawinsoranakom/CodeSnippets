def test_create_basic_progress(self):
        """Test creating a basic progress object."""
        progress = MigrationProgress(
            es_index="ragflow_test",
            ob_table="ragflow_test",
        )

        assert progress.es_index == "ragflow_test"
        assert progress.ob_table == "ragflow_test"
        assert progress.total_documents == 0
        assert progress.migrated_documents == 0
        assert progress.status == "pending"
        assert progress.started_at != ""
        assert progress.updated_at != ""