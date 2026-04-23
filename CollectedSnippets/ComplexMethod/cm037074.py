def _rope_scaling_validation(self):
        """
        Validate the `rope_scaling` configuration.
        """
        if self.rope_scaling is None:
            return

        if not isinstance(self.rope_scaling, dict) or len(self.rope_scaling) != 2:
            raise ValueError(
                "`rope_scaling` must be a dictionary with with two fields, `type` and "
                f"`factor` or `type` and `alpha`, got {self.rope_scaling}"
            )
        rope_scaling_type = self.rope_scaling.get("type", None)
        rope_scaling_factor = self.rope_scaling.get("factor", None)
        rope_scaling_alpha = self.rope_scaling.get("alpha", None)
        if rope_scaling_type is None or rope_scaling_type not in ["linear", "dynamic"]:
            raise ValueError(
                "`rope_scaling`'s type field must be one of ['linear', 'dynamic'], "
                f"got {rope_scaling_type}"
            )
        if rope_scaling_factor is None and rope_scaling_alpha is None:
            raise ValueError(
                "`rope_scaling`'s factor or alpha field must be have one, "
                "got both of none"
            )
        if rope_scaling_factor is not None and (
            not isinstance(rope_scaling_factor, float) or rope_scaling_factor <= 1.0
        ):
            raise ValueError(
                "`rope_scaling`'s factor field must be a float > 1.0, "
                f"got {rope_scaling_factor}"
            )
        if rope_scaling_alpha is not None and (
            not isinstance(rope_scaling_alpha, float) or rope_scaling_alpha <= 1.0
        ):
            raise ValueError(
                "`rope_scaling`'s alpha field must be a float > 1.0, "
                f"got {rope_scaling_alpha}"
            )