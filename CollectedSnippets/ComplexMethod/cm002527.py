def verify_out_features_out_indices(self):
        """
        Verify that out_indices and out_features are valid for the given stage_names.
        """
        if self.stage_names is None:
            raise ValueError("Stage_names must be set for transformers backbones")

        if self._out_features is not None:
            if not isinstance(self._out_features, (list,)):
                raise ValueError(f"out_features must be a list got {type(self._out_features)}")
            if any(feat not in self.stage_names for feat in self._out_features):
                raise ValueError(
                    f"out_features must be a subset of stage_names: {self.stage_names} got {self._out_features}"
                )
            if len(self._out_features) != len(set(self._out_features)):
                raise ValueError(f"out_features must not contain any duplicates, got {self._out_features}")
            if self._out_features != (
                sorted_feats := [feat for feat in self.stage_names if feat in self._out_features]
            ):
                raise ValueError(
                    f"out_features must be in the same order as stage_names, expected {sorted_feats} got {self._out_features}"
                )

        if self._out_indices is not None:
            if not isinstance(self._out_indices, list):
                raise ValueError(f"out_indices must be a list, got {type(self._out_indices)}")
            # Convert negative indices to their positive equivalent: [-1,] -> [len(stage_names) - 1,]
            positive_indices = tuple(idx % len(self.stage_names) if idx < 0 else idx for idx in self._out_indices)
            if any(idx for idx in positive_indices if idx not in range(len(self.stage_names))):
                raise ValueError(
                    f"out_indices must be valid indices for stage_names {self.stage_names}, got {self._out_indices}"
                )
            if len(positive_indices) != len(set(positive_indices)):
                msg = f"out_indices must not contain any duplicates, got {self._out_indices}"
                msg += f"(equivalent to {positive_indices}))" if positive_indices != self._out_indices else ""
                raise ValueError(msg)
            if positive_indices != tuple(sorted(positive_indices)):
                sorted_negative = [
                    idx for _, idx in sorted(zip(positive_indices, self._out_indices), key=lambda x: x[0])
                ]
                raise ValueError(
                    f"out_indices must be in the same order as stage_names, expected {sorted_negative} got {self._out_indices}"
                )

        if self._out_features is not None and self._out_indices is not None:
            if len(self._out_features) != len(self._out_indices):
                raise ValueError("out_features and out_indices should have the same length if both are set")
            if self._out_features != [self.stage_names[idx] for idx in self._out_indices]:
                raise ValueError("out_features and out_indices should correspond to the same stages if both are set")