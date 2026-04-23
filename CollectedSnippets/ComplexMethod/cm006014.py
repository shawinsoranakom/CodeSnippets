def test_similarity_search(
        self, component_class: type[MongoVectorStoreComponent], default_kwargs: dict[str, Any]
    ) -> None:
        """Test the similarity search functionality."""
        # Create test data with distinct topics
        test_data = [
            "The quick brown fox jumps over the lazy dog",
            "Python is a popular programming language",
            "Machine learning models process data",
            "The lazy dog sleeps all day long",
        ]
        default_kwargs["ingest_data"] = [Data(data={"text": text, "metadata": {}}) for text in test_data]
        default_kwargs["number_of_results"] = 2
        default_kwargs["insert_mode"] = "overwrite"

        # Create and initialize the component
        component: MongoVectorStoreComponent = component_class().set(**default_kwargs)

        # Build the vector store first to ensure data is ingested
        vector_store = component.build_vector_store()
        assert vector_store is not None

        # Verify documents were stored with embeddings
        documents = list(vector_store._collection.find({}))
        assert len(documents) == len(test_data)
        for doc in documents:
            assert "embedding" in doc
            assert isinstance(doc["embedding"], list)
            assert len(doc["embedding"]) == 8  # Should match our embedding size

        self.__create_search_index(component_class, vector_store._collection, default_kwargs)

        # Verify index was created
        indexes = vector_store._collection.list_search_indexes()
        index_names = [idx["name"] for idx in indexes]
        assert default_kwargs["index_name"] in index_names

        # Test similarity search through the component
        component.set(search_query="dog")
        results = component.search_documents()
        time.sleep(5)  # wait the results come from API

        assert len(results) == 2, "Expected 2 results for 'lazy dog' query"
        # The most relevant results should be about dogs
        assert any("dog" in result.data["text"].lower() for result in results)

        # Test with different number of results
        component.set(number_of_results=3)
        results = component.search_documents()
        assert len(results) == 3
        assert all("text" in result.data for result in results)