def test_valid_relationship(self):
        attrs = ['"relationship"', "Alice", "Bob", "friends with", "friendship", "2.0"]
        result = handle_single_relationship_extraction(attrs, "chunk1")
        assert result is not None
        assert result["src_id"] == "ALICE"
        assert result["tgt_id"] == "BOB"
        assert result["weight"] == 2.0
        assert result["description"] == "friends with"
        assert result["keywords"] == "friendship"
        assert result["source_id"] == "chunk1"
        assert "created_at" in result["metadata"]