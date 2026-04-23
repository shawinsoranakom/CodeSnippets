def _ensure_embedding_field_mapping(
        self,
        client: OpenSearch,
        index_name: str,
        field_name: str,
        dim: int,
        engine: str,
        space_type: str,
        ef_construction: int,
        m: int,
    ) -> None:
        """Lazily add a dynamic embedding field to the index if it doesn't exist.

        This allows adding new embedding models without recreating the entire index.
        Also ensures the embedding_model tracking field exists.

        Note: Some OpenSearch versions/configurations have issues with dynamically adding
        knn_vector mappings (NullPointerException). This method checks if the field
        already exists before attempting to add it, and gracefully skips if the field
        is already properly configured.

        Args:
            client: OpenSearch client instance
            index_name: Target index name
            field_name: Dynamic field name for this embedding model
            dim: Vector dimensionality
            engine: Vector search engine
            space_type: Distance metric
            ef_construction: Construction parameter
            m: HNSW parameter
        """
        # First, check if the field already exists and is properly mapped
        properties = self._get_index_properties(client)
        if self._is_knn_vector_field(properties, field_name):
            # Field already exists as knn_vector - verify dimensions match
            existing_dim = self._get_field_dimension(properties, field_name)
            if existing_dim is not None and existing_dim != dim:
                logger.warning(
                    f"Field '{field_name}' exists with dimension {existing_dim}, "
                    f"but current embedding has dimension {dim}. Using existing mapping."
                )
            else:
                logger.info(
                    f"[OpenSearchMultimodel] Field '{field_name}' already exists"
                    f"as knn_vector with matching dimensions - skipping mapping update"
                )
            return

        # Field doesn't exist, try to add the mapping
        try:
            mapping = {
                "properties": {
                    field_name: {
                        "type": "knn_vector",
                        "dimension": dim,
                        "method": {
                            "name": "disk_ann",
                            "space_type": space_type,
                            "engine": engine,
                            "parameters": {"ef_construction": ef_construction, "m": m},
                        },
                    },
                    # Also ensure the embedding_model tracking field exists as keyword
                    "embedding_model": {"type": "keyword"},
                    "embedding_dimensions": {"type": "integer"},
                }
            }
            client.indices.put_mapping(index=index_name, body=mapping)
            logger.info(f"Added/updated embedding field mapping: {field_name}")
        except RequestError as e:
            error_str = str(e).lower()
            if "invalid engine" in error_str and "jvector" in error_str:
                msg = (
                    "The 'jvector' engine is not available in your OpenSearch installation. "
                    "Use 'nmslib' or 'faiss' for standard OpenSearch, or upgrade to OpenSearch 2.9+."
                )
                raise ValueError(msg) from e
            if "index.knn" in error_str:
                msg = (
                    "The index has index.knn: false. Delete the existing index and let the "
                    "component recreate it, or create a new index with a different name."
                )
                raise ValueError(msg) from e
            raise
        except Exception as e:
            # Check if this is the known OpenSearch k-NN NullPointerException issue
            error_str = str(e).lower()
            if "null" in error_str or "nullpointerexception" in error_str:
                logger.warning(
                    f"[OpenSearchMultimodel] Could not add embedding field mapping for {field_name}"
                    f"due to OpenSearch k-NN plugin issue: {e}. "
                    f"This is a known issue with some OpenSearch versions. "
                    f"[OpenSearchMultimodel] Skipping mapping update. "
                    f"Please ensure the index has the correct mapping for KNN search to work."
                )
                # Skip and continue - ingestion will proceed, but KNN search may fail if mapping doesn't exist
                return
            logger.warning(f"[OpenSearchMultimodel] Could not add embedding field mapping for {field_name}: {e}")
            raise

        # Verify the field was added correctly
        properties = self._get_index_properties(client)
        if not self._is_knn_vector_field(properties, field_name):
            msg = f"Field '{field_name}' is not mapped as knn_vector. Current mapping: {properties.get(field_name)}"
            logger.error(msg)
            raise ValueError(msg)