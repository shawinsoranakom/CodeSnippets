def test_build_config_update(self, component_class: type[LocalDBComponent]) -> None:
        """Test the update_build_config method."""
        component = component_class()

        # Test mode=Ingest
        build_config = {
            "ingest_data": {"show": False},
            "collection_name": {"show": False},
            "persist": {"show": False},
            "persist_directory": {"show": False},
            "embedding": {"show": False},
            "allow_duplicates": {"show": False},
            "limit": {"show": False},
            "search_query": {"show": False},
            "search_type": {"show": False},
            "number_of_results": {"show": False},
            "existing_collections": {"show": False},
        }

        updated_config = component.update_build_config(build_config, "Ingest", "mode")

        assert updated_config["ingest_data"]["show"] is True
        assert updated_config["collection_name"]["show"] is True
        assert updated_config["persist"]["show"] is True
        assert updated_config["search_query"]["show"] is False

        # Test mode=Retrieve
        updated_config = component.update_build_config(build_config, "Retrieve", "mode")

        assert updated_config["search_query"]["show"] is True
        assert updated_config["search_type"]["show"] is True
        assert updated_config["number_of_results"]["show"] is True
        assert updated_config["existing_collections"]["show"] is True
        assert updated_config["collection_name"]["show"] is False

        # Test persist=True/False
        build_config = {"persist_directory": {"show": False}}
        # Use keyword arguments to fix FBT003
        updated_config = component.update_build_config(build_config, field_value=True, field_name="persist")
        assert updated_config["persist_directory"]["show"] is True

        updated_config = component.update_build_config(build_config, field_value=False, field_name="persist")
        assert updated_config["persist_directory"]["show"] is False

        # Test existing_collections update
        # Fix the dict entry type issue
        build_config = {"collection_name": {"value": "old_name", "show": False}}
        updated_config = component.update_build_config(build_config, "new_collection", "existing_collections")
        assert updated_config["collection_name"]["value"] == "new_collection"