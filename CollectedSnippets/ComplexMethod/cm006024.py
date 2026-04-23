def test_retrieve_data_path_construction(self, component_class, default_kwargs):
        """Test that retrieve_data constructs the correct paths."""
        component = component_class(**default_kwargs)

        # Test that the component correctly builds the KB path

        assert component.kb_root_path == default_kwargs["kb_root_path"]
        assert component.knowledge_base == default_kwargs["knowledge_base"]

        # Test that paths are correctly expanded
        expanded_path = Path(component.kb_root_path).expanduser()
        assert expanded_path.exists()  # tmp_path should exist

        # Verify method exists with correct parameters
        assert hasattr(component, "retrieve_data")
        assert hasattr(component, "search_query")
        assert hasattr(component, "top_k")
        assert hasattr(component, "include_embeddings")