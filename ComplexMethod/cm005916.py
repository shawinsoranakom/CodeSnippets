def test_filter_by_tag_with_field_selection(self):
        """Test combining tag filter with field selection."""
        all_tags = get_all_tags()
        if len(all_tags) > 0:
            test_tag = all_tags[0]
            results = list_templates(tags=[test_tag], fields=["name", "tags"])

            assert len(results) > 0
            for result in results:
                assert "name" in result
                assert "tags" in result
                assert "description" not in result
                assert "data" not in result
                assert test_tag in result["tags"]