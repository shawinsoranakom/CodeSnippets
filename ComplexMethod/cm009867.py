def from_llm(
        cls,
        llm: BaseLanguageModel,
        *,
        prompt: PromptTemplate | None = None,
        criteria: CRITERIA_TYPE | str | None = None,
        normalize_by: float | None = None,
        **kwargs: Any,
    ) -> ScoreStringEvalChain:
        """Initialize the ScoreStringEvalChain from an LLM.

        Args:
            llm: The LLM to use (GPT-4 recommended).
            prompt: The prompt to use.
            criteria: The criteria to use.
            normalize_by: The value to normalize the score by.
            **kwargs: Additional keyword arguments.

        Returns:
            The initialized ScoreStringEvalChain.

        Raises:
            ValueError: If the input variables are not as expected.

        """
        if not (hasattr(llm, "model_name") and not llm.model_name.startswith("gpt-4")):
            logger.warning(
                "This chain was only tested with GPT-4. \
Performance may be significantly worse with other models.",
            )

        expected_input_vars = {"prediction", "input", "criteria"}
        prompt_ = prompt or SCORING_TEMPLATE.partial(reference="")
        if expected_input_vars != set(prompt_.input_variables):
            msg = (
                f"Input variables should be {expected_input_vars}, "
                f"but got {prompt_.input_variables}"
            )
            raise ValueError(msg)
        criteria_ = resolve_criteria(criteria)
        criteria_str = "\n".join(
            f"{k}: {v}" if v else k for k, v in criteria_.items()
        ).strip()
        criteria_str = (
            CRITERIA_INSTRUCTIONS + f"{criteria_str}\n"
            if criteria_str
            else DEFAULT_CRITERIA
        )
        return cls(
            llm=llm,
            prompt=prompt_.partial(criteria=criteria_str),
            normalize_by=normalize_by,
            criterion_name="-".join(criteria_),
            **kwargs,
        )