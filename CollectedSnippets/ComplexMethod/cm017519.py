def __init__(
        self,
        vector,
        query,
        weights=None,
        normalization=None,
        cover_density=False,
    ):
        from .fields.array import ArrayField

        if not hasattr(vector, "resolve_expression"):
            vector = SearchVector(vector)
        if not hasattr(query, "resolve_expression"):
            query = SearchQuery(query)
        expressions = [vector, query]
        if weights is not None:
            if not hasattr(weights, "resolve_expression"):
                weights = Value(weights)
            weights = Cast(weights, ArrayField(_Float4Field()))
            expressions = [weights, *expressions]
        if normalization is not None:
            if not hasattr(normalization, "resolve_expression"):
                normalization = Value(normalization)
            expressions.append(normalization)
        if cover_density:
            self.function = "ts_rank_cd"
        super().__init__(*expressions)