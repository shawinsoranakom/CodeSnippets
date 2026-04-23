def _configure_search_options(self, build_config: dict) -> dict:
        """Configure hybrid search, reranker, and vector search options."""
        # Detect available hybrid search capabilities
        hybrid_capabilities = self._detect_hybrid_capabilities()

        # Return if we haven't selected a collection
        if not build_config["collection_name"]["options"] or not build_config["collection_name"]["value"]:
            return build_config

        # Get collection options
        collection_options = self._get_collection_options(build_config)

        # Get the selected collection index
        index = build_config["collection_name"]["options"].index(build_config["collection_name"]["value"])
        provider = build_config["collection_name"]["options_metadata"][index]["provider"]
        build_config["embedding_model"]["show"] = not bool(provider)
        build_config["embedding_model"]["required"] = not bool(provider)

        # Determine search configuration
        is_vector_search = build_config["search_method"]["value"] == "Vector Search"
        is_autodetect = build_config["autodetect_collection"]["value"]

        # Apply hybrid search configuration
        if hybrid_capabilities["available"]:
            build_config["search_method"]["show"] = True
            build_config["search_method"]["options"] = ["Hybrid Search", "Vector Search"]
            build_config["search_method"]["value"] = build_config["search_method"].get("value", "Hybrid Search")

            build_config["reranker"]["options"] = hybrid_capabilities["reranker_models"]
            build_config["reranker"]["options_metadata"] = hybrid_capabilities["reranker_metadata"]
            if hybrid_capabilities["reranker_models"]:
                build_config["reranker"]["value"] = hybrid_capabilities["reranker_models"][0]
        else:
            build_config["search_method"]["show"] = False
            build_config["search_method"]["options"] = ["Vector Search"]
            build_config["search_method"]["value"] = "Vector Search"
            build_config["reranker"]["options"] = []
            build_config["reranker"]["options_metadata"] = []

        # Configure reranker visibility and state
        hybrid_enabled = (
            collection_options["rerank_enabled"] and build_config["search_method"]["value"] == "Hybrid Search"
        )

        build_config["reranker"]["show"] = hybrid_enabled
        build_config["reranker"]["toggle_value"] = hybrid_enabled
        build_config["reranker"]["toggle_disable"] = is_vector_search

        # Configure lexical terms
        lexical_visible = collection_options["lexical_enabled"] and not is_vector_search
        build_config["lexical_terms"]["show"] = lexical_visible
        build_config["lexical_terms"]["value"] = "" if is_vector_search else build_config["lexical_terms"]["value"]

        # Configure search type and score threshold
        build_config["search_type"]["show"] = is_vector_search
        build_config["search_score_threshold"]["show"] = is_vector_search

        # Force similarity search for hybrid mode or autodetect
        if hybrid_enabled or is_autodetect:
            build_config["search_type"]["value"] = "Similarity"

        return build_config