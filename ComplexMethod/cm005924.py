def test_qdrant_component_directly_importable(self):
        """Regression test for Qdrant component import (deprecated import fix).

        This test specifically validates that the Qdrant component can be
        imported after fixing the deprecated langchain.embeddings.base import.
        """
        try:
            from lfx.components.qdrant import QdrantVectorStoreComponent

            # Verify it's a class
            assert isinstance(QdrantVectorStoreComponent, type)

            # Verify it has expected attributes
            assert hasattr(QdrantVectorStoreComponent, "display_name")
            assert QdrantVectorStoreComponent.display_name == "Qdrant"

        except ImportError as e:
            if "qdrant_client" in str(e) or "langchain_community" in str(e):
                pytest.skip("Qdrant dependencies not installed (expected in test environment)")
            pytest.fail(f"Failed to import QdrantVectorStoreComponent: {e}")
        except AttributeError as e:
            if "Could not import" in str(e):
                pytest.skip("Qdrant dependencies not installed (expected in test environment)")
            raise