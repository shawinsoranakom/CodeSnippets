def validate(self, strict=False):
        """
        Validates the values of the attributes of the [`GenerationConfig`] instance. Raises exceptions in the presence
        of parameterization that can be detected as incorrect from the configuration instance alone.

        Note that some parameters not validated here are best validated at generate runtime, as they may depend on
        other inputs and/or the model, such as parameters related to the generation length.

        Args:
            strict (bool): If True, raise an exception for any issues found. If False, only log issues.
        """
        minor_issues = {}  # format: {attribute_name: issue_description}

        # 1. Validation of individual attributes
        # 1.1. Decoding attributes
        if self.early_stopping not in {None, True, False, "never"}:
            raise ValueError(f"`early_stopping` must be a boolean or 'never', but is {self.early_stopping}.")
        if self.max_new_tokens is not None and self.max_new_tokens <= 0:
            raise ValueError(f"`max_new_tokens` must be greater than 0, but is {self.max_new_tokens}.")
        if self.pad_token_id is not None and self.pad_token_id < 0:
            minor_issues["pad_token_id"] = (
                f"`pad_token_id` should be positive but got {self.pad_token_id}. This will cause errors when batch "
                "generating, if there is padding. Please set `pad_token_id` explicitly as "
                "`model.generation_config.pad_token_id=PAD_TOKEN_ID` to avoid errors in generation"
            )
        # 1.2. Cache attributes
        # "paged" re-routes to continuous batching and so it is a valid cache implementation. But we do not want to test
        # it with the `generate` as the other would be, so we we cannot add it to ALL_CACHE_IMPLEMENTATIONS
        valid_cache_implementations = ALL_CACHE_IMPLEMENTATIONS + ("paged",)
        if self.cache_implementation is not None and self.cache_implementation not in valid_cache_implementations:
            raise ValueError(
                f"Invalid `cache_implementation` ({self.cache_implementation}). Choose one of: "
                f"{valid_cache_implementations}"
            )
        # 1.3. Performance attributes
        if self.compile_config is not None and not isinstance(self.compile_config, CompileConfig):
            raise ValueError(
                f"You provided `compile_config` as an instance of {type(self.compile_config)}, but it must be an "
                "instance of `CompileConfig`."
            )
        # 1.4. Watermarking attributes
        if self.watermarking_config is not None:
            self.watermarking_config.validate()

        # 2. Validation of attribute combinations
        # 2.1. detect sampling-only parameterization when not in sampling mode

        # Note that we check `is not True` in purpose. Boolean fields can also be `None` so we
        # have to be explicit. Value of `None` is same as having `False`, i.e. the default value
        if self.do_sample is not True:
            greedy_wrong_parameter_msg = (
                "`do_sample` is set not to set `True`. However, `{flag_name}` is set to `{flag_value}` -- this flag is only "
                "used in sample-based generation modes. You should set `do_sample=True` or unset `{flag_name}`."
            )
            if self.temperature is not None and self.temperature != 1.0:
                minor_issues["temperature"] = greedy_wrong_parameter_msg.format(
                    flag_name="temperature", flag_value=self.temperature
                )
            if self.top_p is not None and self.top_p != 1.0:
                minor_issues["top_p"] = greedy_wrong_parameter_msg.format(flag_name="top_p", flag_value=self.top_p)
            if self.min_p is not None:
                minor_issues["min_p"] = greedy_wrong_parameter_msg.format(flag_name="min_p", flag_value=self.min_p)
            if self.top_h is not None:
                minor_issues["top_h"] = greedy_wrong_parameter_msg.format(flag_name="top_h", flag_value=self.top_h)
            if self.typical_p is not None and self.typical_p != 1.0:
                minor_issues["typical_p"] = greedy_wrong_parameter_msg.format(
                    flag_name="typical_p", flag_value=self.typical_p
                )
            if self.top_k is not None and self.top_k != 50:
                minor_issues["top_k"] = greedy_wrong_parameter_msg.format(flag_name="top_k", flag_value=self.top_k)
            if self.epsilon_cutoff is not None and self.epsilon_cutoff != 0.0:
                minor_issues["epsilon_cutoff"] = greedy_wrong_parameter_msg.format(
                    flag_name="epsilon_cutoff", flag_value=self.epsilon_cutoff
                )
            if self.eta_cutoff is not None and self.eta_cutoff != 0.0:
                minor_issues["eta_cutoff"] = greedy_wrong_parameter_msg.format(
                    flag_name="eta_cutoff", flag_value=self.eta_cutoff
                )

        # 2.2. detect beam-only parameterization when not in beam mode
        if self.num_beams is None or self.num_beams == 1:
            single_beam_wrong_parameter_msg = (
                "`num_beams` is set to {num_beams}. However, `{flag_name}` is set to `{flag_value}` -- this flag is only used "
                "in beam-based generation modes. You should set `num_beams>1` or unset `{flag_name}`."
            )
            if self.early_stopping is not None and self.early_stopping is not False:
                minor_issues["early_stopping"] = single_beam_wrong_parameter_msg.format(
                    num_beams=self.num_beams, flag_name="early_stopping", flag_value=self.early_stopping
                )
            if self.length_penalty is not None and self.length_penalty != 1.0:
                minor_issues["length_penalty"] = single_beam_wrong_parameter_msg.format(
                    num_beams=self.num_beams, flag_name="length_penalty", flag_value=self.length_penalty
                )

        # 2.4. check `num_return_sequences`
        if self.num_return_sequences is not None and self.num_return_sequences > 1:
            if self.num_beams is None or self.num_beams == 1:
                if not self.do_sample:
                    raise ValueError(
                        "Greedy methods (do_sample != True) without beam search do not support "
                        f"`num_return_sequences` different than 1 (got {self.num_return_sequences})."
                    )
            elif (
                self.num_beams is not None
                and self.num_return_sequences is not None
                and self.num_return_sequences > self.num_beams
            ):
                raise ValueError(
                    f"`num_return_sequences` ({self.num_return_sequences}) has to be smaller or equal to `num_beams` "
                    f"({self.num_beams})."
                )

        # 2.5. check cache-related arguments
        if self.use_cache is False:
            # In this case, all cache-related arguments should be unset. However, since `use_cache=False` is often used
            # passed to `generate` directly to hot-fix cache issues, let's raise a warning instead of an error
            # (otherwise a user might need to overwrite several parameters).
            no_cache_warning = (
                "You have not set `use_cache` to `True`, but {cache_arg} is set to {cache_arg_value}."
                "{cache_arg} will have no effect."
            )
            for arg_name in ("cache_implementation", "cache_config"):
                if getattr(self, arg_name) is not None:
                    minor_issues[arg_name] = no_cache_warning.format(
                        cache_arg=arg_name, cache_arg_value=getattr(self, arg_name)
                    )

        # 2.6. other incorrect combinations
        if self.return_dict_in_generate is not True:
            for extra_output_flag in self.extra_output_flags:
                if getattr(self, extra_output_flag) is True:
                    minor_issues[extra_output_flag] = (
                        f"`return_dict_in_generate` is NOT set to `True`, but `{extra_output_flag}` is. When "
                        f"`return_dict_in_generate` is not `True`, `{extra_output_flag}` is ignored."
                    )

        # 3. Check common issue: passing `generate` arguments inside the generation config
        generate_arguments = (
            "logits_processor",
            "stopping_criteria",
            "prefix_allowed_tokens_fn",
            "synced_gpus",
            "assistant_model",
            "streamer",
            "negative_prompt_ids",
            "negative_prompt_attention_mask",
        )
        for arg in generate_arguments:
            if hasattr(self, arg):
                raise ValueError(
                    f"Argument `{arg}` is not a valid argument of `GenerationConfig`. It should be passed to "
                    "`generate()` (or a pipeline) directly."
                )

        # Finally, handle caught minor issues. With default parameterization, we will throw a minimal warning.
        if len(minor_issues) > 0:
            # Full list of issues with potential fixes
            info_message = []
            for attribute_name, issue_description in minor_issues.items():
                info_message.append(f"- `{attribute_name}`: {issue_description}")
            info_message = "\n".join(info_message)
            info_message += (
                "\nIf you're using a pretrained model, note that some of these attributes may be set through the "
                "model's `generation_config.json` file."
            )

            if strict:
                raise ValueError("GenerationConfig is invalid: \n" + info_message)
            else:
                attributes_with_issues = list(minor_issues.keys())
                warning_message = (
                    f"The following generation flags are not valid and may be ignored: {attributes_with_issues}."
                )
                if logging.get_verbosity() >= logging.WARNING:
                    warning_message += " Set `TRANSFORMERS_VERBOSITY=info` for more details."
                logger.warning_once(warning_message)
                logger.info_once(info_message)