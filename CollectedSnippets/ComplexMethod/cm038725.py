def get_diff_sampling_param(self) -> dict[str, Any]:
        """
        This method returns a dictionary containing the non-default sampling
        parameters with `override_generation_config` applied.

        The default sampling parameters are:

        - vLLM's neutral defaults if `self.generation_config="vllm"`
        - the model's defaults if `self.generation_config="auto"`
        - as defined in `generation_config.json` if
            `self.generation_config="path/to/generation_config/dir"`

        Returns:
            A dictionary containing the non-default sampling parameters.
        """
        src = self.generation_config

        config = {} if src == "vllm" else self.try_get_generation_config()

        # Overriding with given generation config
        config.update(self.override_generation_config)

        available_params = [
            "repetition_penalty",
            "temperature",
            "top_k",
            "top_p",
            "min_p",
            "max_new_tokens",
        ]
        if any(p in config for p in available_params):
            diff_sampling_param = {
                p: config.get(p) for p in available_params if config.get(p) is not None
            }
            # Huggingface definition of max_new_tokens is equivalent
            # to vLLM's max_tokens
            if "max_new_tokens" in diff_sampling_param:
                diff_sampling_param["max_tokens"] = diff_sampling_param.pop(
                    "max_new_tokens"
                )
        else:
            diff_sampling_param = {}

        if diff_sampling_param and src != "vllm":
            logger.warning_once(
                "Default vLLM sampling parameters have been overridden by %s: `%s`. "
                "If this is not intended, please relaunch vLLM instance "
                "with `--generation-config vllm`.",
                "the model's `generation_config.json`" if src == "auto" else src,
                str(diff_sampling_param),
                scope="local",
            )

        return diff_sampling_param