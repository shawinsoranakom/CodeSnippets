def __post_init__(self, **kwargs):
        self.context_length = self.context_length or self.prediction_length
        self.lags_sequence = self.lags_sequence if self.lags_sequence is not None else [1, 2, 3, 4, 5, 6, 7]

        if not (self.cardinality and self.num_static_categorical_features > 0):
            self.cardinality = [0]

        if not (self.embedding_dimension and self.num_static_categorical_features > 0):
            self.embedding_dimension = [min(50, (cat + 1) // 2) for cat in self.cardinality]

        self.feature_size = self.input_size * len(self.lags_sequence) + self._number_of_features
        super().__post_init__(**kwargs)