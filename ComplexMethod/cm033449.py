def test_ragflow_columns_types(self):
        """Test column type definitions."""
        # Primary key
        assert RAGFLOW_COLUMNS["id"]["is_primary"] is True
        assert RAGFLOW_COLUMNS["id"]["nullable"] is False

        # Indexed columns
        assert RAGFLOW_COLUMNS["kb_id"]["index"] is True
        assert RAGFLOW_COLUMNS["doc_id"]["index"] is True

        # Array columns
        assert RAGFLOW_COLUMNS["important_kwd"]["is_array"] is True
        assert RAGFLOW_COLUMNS["question_kwd"]["is_array"] is True

        # JSON columns
        assert RAGFLOW_COLUMNS["metadata"]["is_json"] is True
        assert RAGFLOW_COLUMNS["extra"]["is_json"] is True