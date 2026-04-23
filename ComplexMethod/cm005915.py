def test_list_with_multiple_fields(self):
        """Test listing with multiple field selection."""
        templates = list_templates(fields=["id", "name", "description", "tags"])

        assert len(templates) > 0
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "tags" in template
            assert "data" not in template