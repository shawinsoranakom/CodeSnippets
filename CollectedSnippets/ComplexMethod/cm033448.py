def test_get_resume_info(self, manager):
        """Test getting resume information."""
        progress = manager.create_progress(
            es_index="ragflow_info",
            ob_table="ragflow_info",
            total_documents=1000,
        )
        progress.migrated_documents = 500
        progress.last_sort_values = ["doc_500", 12345]
        progress.schema_converted = True
        progress.table_created = True
        manager.save_progress(progress)

        info = manager.get_resume_info("ragflow_info", "ragflow_info")

        assert info is not None
        assert info["migrated_documents"] == 500
        assert info["total_documents"] == 1000
        assert info["last_sort_values"] == ["doc_500", 12345]
        assert info["schema_converted"] is True
        assert info["table_created"] is True
        assert info["status"] == "running"