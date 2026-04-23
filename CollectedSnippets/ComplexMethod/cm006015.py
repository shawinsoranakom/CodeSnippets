def test_chroma_collection_to_data(
        self, component_class: type[ChromaVectorStoreComponent], default_kwargs: dict[str, Any]
    ) -> None:
        """Test the chroma_collection_to_data function."""
        from lfx.base.vectorstores.utils import chroma_collection_to_data

        # Create a collection with documents and metadata
        test_data = [
            Data(data={"text": "Document 1", "metadata_field": "value1"}),
            Data(data={"text": "Document 2", "metadata_field": "value2"}),
        ]
        default_kwargs["ingest_data"] = test_data
        component: ChromaVectorStoreComponent = component_class().set(**default_kwargs)
        vector_store = component.build_vector_store()

        # Get the collection data
        collection_dict = vector_store.get()
        data_objects = chroma_collection_to_data(collection_dict)

        # Verify the conversion
        assert len(data_objects) == 2
        for data_obj in data_objects:
            assert isinstance(data_obj, Data)
            assert "id" in data_obj.data
            assert "text" in data_obj.data
            assert data_obj.data["text"] in {"Document 1", "Document 2"}
            assert "metadata_field" in data_obj.data
            assert data_obj.data["metadata_field"] in {"value1", "value2"}