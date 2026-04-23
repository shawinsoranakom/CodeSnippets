def __init__(
        self,
        features,
        output_mode="concat",
        crosses=None,
        crossing_dim=32,
        hashing_dim=32,
        num_discretization_bins=32,
        name=None,
    ):
        super().__init__(name=name)
        if not features:
            raise ValueError("The `features` argument cannot be None or empty.")
        self.crossing_dim = crossing_dim
        self.hashing_dim = hashing_dim
        self.num_discretization_bins = num_discretization_bins
        self.features = {
            name: self._standardize_feature(name, value)
            for name, value in features.items()
        }
        self.crosses = []
        if crosses:
            feature_set = set(features.keys())
            for cross in crosses:
                if isinstance(cross, dict):
                    cross = serialization_lib.deserialize_keras_object(cross)
                if isinstance(cross, Cross):
                    self.crosses.append(cross)
                else:
                    if not crossing_dim:
                        raise ValueError(
                            "When specifying `crosses`, the argument "
                            "`crossing_dim` "
                            "(dimensionality of the crossing space) "
                            "should be specified as well."
                        )
                    for key in cross:
                        if key not in feature_set:
                            raise ValueError(
                                "All features referenced "
                                "in the `crosses` argument "
                                "should be present in the `features` dict. "
                                f"Received unknown features: {cross}"
                            )
                    self.crosses.append(Cross(cross, crossing_dim=crossing_dim))
        self.crosses_by_name = {cross.name: cross for cross in self.crosses}

        if output_mode not in {"dict", "concat"}:
            raise ValueError(
                "Invalid value for argument `output_mode`. "
                "Expected one of {'dict', 'concat'}. "
                f"Received: output_mode={output_mode}"
            )
        self.output_mode = output_mode

        self.inputs = {
            name: self._feature_to_input(name, value)
            for name, value in self.features.items()
        }
        self.preprocessors = {
            name: value.preprocessor for name, value in self.features.items()
        }
        self.encoded_features = None
        self.crossers = {
            cross.name: self._cross_to_crosser(cross) for cross in self.crosses
        }
        self.one_hot_encoders = {}
        self._is_adapted = False
        self.concat = None
        self._preprocessed_features_names = None
        self._crossed_features_names = None
        self._sublayers_built = False