def _select_relevance_score_fn(self) -> Callable[[float], float]:
        """Select the relevance score function based on collections distance metric.

        The most similar documents will have the lowest relevance score. Default
        relevance score function is Euclidean distance. Distance metric must be
        provided in `collection_configuration` during initialization of Chroma object.
        Example: collection_configuration={"hnsw": {"space": "cosine"}}.
        Available distance metrics are: 'cosine', 'l2' and 'ip'.

        Returns:
            The relevance score function.

        Raises:
            ValueError: If the distance metric is not supported.
        """
        if self.override_relevance_score_fn:
            return self.override_relevance_score_fn

        hnsw_config = self._collection.configuration.get("hnsw")
        hnsw_distance: str | None = hnsw_config.get("space") if hnsw_config else None

        spann_config = self._collection.configuration.get("spann")
        spann_distance: str | None = spann_config.get("space") if spann_config else None

        distance = hnsw_distance or spann_distance

        if distance == "cosine":
            return self._cosine_relevance_score_fn
        if distance == "l2":
            return self._euclidean_relevance_score_fn
        if distance == "ip":
            return self._max_inner_product_relevance_score_fn
        msg = (
            "No supported normalization function"
            f" for distance metric of type: {distance}."
            "Consider providing relevance_score_fn to Chroma constructor."
        )
        raise ValueError(
            msg,
        )