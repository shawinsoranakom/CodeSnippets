def test_metadata_filtering_with_complex_data(
        self, component_class: type[ChromaVectorStoreComponent], default_kwargs: dict[str, Any]
    ) -> None:
        """Test that complex metadata is properly filtered and simple types are preserved."""
        from langflow.base.vectorstores.utils import chroma_collection_to_data

        # Create test data that covers the original error scenario and validation
        test_data = [
            Data(
                data={
                    "text": "Document with mixed metadata",
                    "files": [],  # This empty list was causing the original ChromaDB error
                    "tags": ["tag1", "tag2"],  # Lists should be filtered out
                    "nested": {"key": "value"},  # Nested objects should be filtered out
                    "simple_string": "preserved",
                    "simple_int": 42,
                    "simple_bool": True,
                    "empty_string": "",  # Edge case: empty but valid
                    "zero_value": 0,  # Edge case: falsy but valid
                }
            )
        ]

        default_kwargs["ingest_data"] = test_data
        default_kwargs["collection_name"] = "test_metadata_filtering"

        # This should not raise an error despite the complex metadata
        component: ChromaVectorStoreComponent = component_class().set(**default_kwargs)
        vector_store = component.build_vector_store()

        # Verify document was added successfully
        collection_dict = vector_store.get()
        assert len(collection_dict["documents"]) == 1
        assert "Document with mixed metadata" in collection_dict["documents"][0]

        # Verify metadata filtering: simple types preserved, complex types filtered out
        data_objects = chroma_collection_to_data(collection_dict)
        data_obj = data_objects[0]

        # Simple types should be preserved
        assert data_obj.data["simple_string"] == "preserved"
        assert data_obj.data["simple_int"] == 42
        assert data_obj.data["simple_bool"] is True
        assert data_obj.data["empty_string"] == ""
        assert data_obj.data["zero_value"] == 0

        # Complex types should be filtered out
        assert "files" not in data_obj.data
        assert "tags" not in data_obj.data
        assert "nested" not in data_obj.data