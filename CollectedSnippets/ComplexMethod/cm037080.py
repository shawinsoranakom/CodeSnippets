def _alibi_scaling_validation(self):
        """
        Validate the `alibi_scaling` configuration.
        """
        if self.alibi_scaling is None:
            return

        if not isinstance(self.alibi_scaling, dict) or len(self.alibi_scaling) != 2:
            raise ValueError(
                "`alibi_scaling` must be a dictionary with two fields, "
                "`type` and `factor` or `type` and `train_seq_len`, "
                f"got {self.alibi_scaling}"
            )
        alibi_scaling_type = self.alibi_scaling.get("type", None)
        alibi_scaling_factor = self.alibi_scaling.get("factor", None)
        alibi_dynamic_scaling = self.alibi_scaling.get("train_seq_len", None)
        if alibi_scaling_type is None or alibi_scaling_type != "linear":
            raise ValueError(
                f"`alibi_scaling`'s type field must be 'linear', "
                f"got {alibi_scaling_type}"
            )
        if (
            alibi_scaling_factor is not None
            and not isinstance(alibi_scaling_factor, float)
            or (alibi_scaling_factor is not None and alibi_scaling_factor <= 1.0)
        ):
            raise ValueError(
                f"`alibi_scaling`'s factor field must be a float > 1.0, "
                f"got {alibi_scaling_factor}"
            )
        if (
            alibi_dynamic_scaling is not None
            and not isinstance(alibi_dynamic_scaling, int)
            or (alibi_dynamic_scaling is not None and alibi_dynamic_scaling <= 1)
        ):
            raise ValueError(
                f"`alibi_scaling`'s `train_seq_len` field must be an "
                f"integer > 1, got {alibi_dynamic_scaling}"
            )