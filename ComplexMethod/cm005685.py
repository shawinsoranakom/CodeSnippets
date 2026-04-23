def post_init(self):
        r"""
        Safety checker that arguments are correct
        """
        if self.bits not in [2, 3, 4, 8]:
            raise ValueError(f"Only support quantization to [2,3,4,8] bits but found {self.bits}")
        if self.group_size != -1 and self.group_size <= 0:
            raise ValueError("group_size must be greater than 0 or equal to -1")
        if not (0 < self.damp_percent < 1):
            raise ValueError("damp_percent must between 0 and 1.")
        if self.dataset is not None:
            if isinstance(self.dataset, str):
                if self.dataset not in ["wikitext2", "c4", "c4-new"]:
                    raise ValueError(
                        f"""You have entered a string value for dataset. You can only choose between
                        ['wikitext2','c4','c4-new'], but we found {self.dataset}"""
                    )
            elif not isinstance(self.dataset, list):
                raise ValueError(
                    f"""dataset needs to be either a list of string or a value in
                    ['wikitext2','c4','c4-new'], but we found {self.dataset}"""
                )

        # act_group_order is only applicable when `desc_act = False`
        if self.desc_act and self.act_group_aware:
            self.act_group_aware = False
            logger.warning("`act_group_aware` has been auto-disabled as it is not compatible with `desc_act = True`.")

        # make sure backend default stays consistent with gptqmodel expectations
        if self.backend is None:
            self.backend = "auto"
        if self.modules_in_block_to_quantize is not None:
            optimum_version = version.parse(importlib.metadata.version("optimum"))
            if optimum_version < version.parse("1.15.0"):
                raise ValueError(
                    "You current version of `optimum` does not support `modules_in_block_to_quantize` quantization argument, please upgrade `optimum` package to a version superior than 1.15.0 ."
                )