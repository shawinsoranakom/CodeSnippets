def from_llm(
        cls,
        llm: BaseLanguageModel,
        *,
        prompt: PromptTemplate | None = None,
        criteria: CRITERIA_TYPE | str | None = None,
        **kwargs: Any,
    ) -> PairwiseStringEvalChain:
        """Initialize the PairwiseStringEvalChain from an LLM.

        Args:
            llm: The LLM to use (GPT-4 recommended).
            prompt: The prompt to use.
            criteria: The criteria to use.
            **kwargs: Additional keyword arguments.

        Returns:
            The initialized PairwiseStringEvalChain.

        Raises:
            ValueError: If the input variables are not as expected.

        """
        # Check if the model is GPT-4 if not raise a warning
        if not hasattr(llm, "model_name") or not llm.model_name.startswith("gpt-4"):
            logger.warning(
                "This chain was only tested with GPT-4. \
Performance may be significantly worse with other models.",
            )

        expected_input_vars = {"prediction", "prediction_b", "input", "criteria"}
        prompt_ = prompt or COMPARISON_TEMPLATE.partial(reference="")
        if expected_input_vars != set(prompt_.input_variables):
            msg = (
                f"Input variables should be {expected_input_vars}, "
                f"but got {prompt_.input_variables}"
            )
            raise ValueError(msg)
        criteria_ = resolve_pairwise_criteria(criteria)
        criteria_str = "\n".join(f"{k}: {v}" if v else k for k, v in criteria_.items())
        criteria_str = CRITERIA_INSTRUCTIONS + criteria_str if criteria_str else ""
        return cls(llm=llm, prompt=prompt_.partial(criteria=criteria_str), **kwargs)