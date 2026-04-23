def get_generation_mode(self, assistant_model: Optional["PreTrainedModel"] = None) -> GenerationMode:
        """
        Returns the generation mode triggered by the [`GenerationConfig`] instance.

        Arg:
            assistant_model (`PreTrainedModel`, *optional*):
                The assistant model to be used for assisted generation. If set, the generation mode will be
                assisted generation.

        Returns:
            `GenerationMode`: The generation mode triggered by the instance.
        """
        # TODO joao: find out a way of not depending on external fields (e.g. `assistant_model`), then make this a
        # property and part of the `__repr__`
        if self.constraints is not None or self.force_words_ids is not None:
            generation_mode = GenerationMode.CONSTRAINED_BEAM_SEARCH
        elif self.num_beams is None or self.num_beams == 1:
            if self.do_sample is not True:
                if (
                    self.top_k is not None
                    and self.top_k > 1
                    and self.penalty_alpha is not None
                    and self.penalty_alpha > 0
                ):
                    generation_mode = GenerationMode.CONTRASTIVE_SEARCH
                else:
                    generation_mode = GenerationMode.GREEDY_SEARCH
            else:
                generation_mode = GenerationMode.SAMPLE
        else:
            if self.num_beam_groups is not None and self.num_beam_groups > 1:
                generation_mode = GenerationMode.GROUP_BEAM_SEARCH
            elif self.do_sample is True:
                generation_mode = GenerationMode.BEAM_SAMPLE
            else:
                generation_mode = GenerationMode.BEAM_SEARCH

        # Assisted generation may extend some generation modes
        if (
            assistant_model is not None
            or self.prompt_lookup_num_tokens is not None
            or self.assistant_early_exit is not None
        ):
            if generation_mode in ("greedy_search", "sample"):
                generation_mode = GenerationMode.ASSISTED_GENERATION
            else:
                logger.warning(
                    "You've set `assistant_model`, which triggers assisted generate. Currently, assisted generate "
                    "is only supported with Greedy Search and Sample. However, the base decoding mode (based on "
                    f"current flags) is {generation_mode} -- some of the set flags will be ignored."
                )

        # DoLa generation may extend some generation modes
        # TODO joao, manuel: remove this in v4.62.0
        if self.dola_layers is not None:
            if generation_mode in ("greedy_search", "sample"):
                generation_mode = GenerationMode.DOLA_GENERATION
            else:
                logger.warning(
                    "You've set `dola_layers`, which triggers DoLa generate. Currently, DoLa generate "
                    "is only supported with Greedy Search and Sample.  However, the base decoding mode (based on "
                    f"current flags) is {generation_mode} -- some of the set flags will be ignored."
                )
        return generation_mode