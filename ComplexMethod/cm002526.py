def set_output_features_output_indices(
        self,
        out_features: list | None,
        out_indices: list | None,
    ):
        """
        Sets output indices and features to new values and aligns them with the given `stage_names`.
        If one of the inputs is not given, find the corresponding `out_features` or `out_indices`
        for the given `stage_names`.

        Args:
            out_features (`list[str]`, *optional*):
                The names of the features for the backbone to output. Defaults to `config._out_features` if not provided.
            out_indices (`list[int]` or `tuple[int]`, *optional*):
                The indices of the features for the backbone to output. Defaults to `config._out_indices` if not provided.
        """
        self._out_features = out_features
        self._out_indices = list(out_indices) if isinstance(out_indices, tuple) else out_indices

        # First verify that the out_features and out_indices are valid
        self.verify_out_features_out_indices()

        # Align output features with indices
        out_features, out_indices = self._out_features, self._out_indices
        if out_indices is None and out_features is None:
            out_indices = [len(self.stage_names) - 1]
            out_features = [self.stage_names[-1]]
        elif out_indices is None and out_features is not None:
            out_indices = [self.stage_names.index(layer) for layer in out_features]
        elif out_features is None and out_indices is not None:
            out_features = [self.stage_names[idx] for idx in out_indices]

        # Update values and verify that the aligned out_features and out_indices are valid
        self._out_features, self._out_indices = out_features, out_indices
        self.verify_out_features_out_indices()