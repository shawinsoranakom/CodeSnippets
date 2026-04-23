def check_structured_outputs_count(cls, data):
        if isinstance(data, ValueError):
            raise data

        if data.get("structured_outputs", None) is None:
            return data

        structured_outputs_kwargs = data["structured_outputs"]
        # structured_outputs may arrive as a dict (from JSON/raw kwargs) or
        # as a StructuredOutputsParams dataclass instance.
        is_dataclass = isinstance(structured_outputs_kwargs, StructuredOutputsParams)
        count = sum(
            (
                getattr(structured_outputs_kwargs, k, None)
                if is_dataclass
                else structured_outputs_kwargs.get(k)
            )
            is not None
            for k in ("json", "regex", "choice")
        )
        # you can only use one kind of constraints for structured outputs
        if count > 1:
            raise ValueError(
                "You can only use one kind of constraints for structured "
                "outputs ('json', 'regex' or 'choice')."
            )
        # you can only either use structured outputs or tools, not both
        if count > 1 and data.get("tool_choice", "none") not in (
            "none",
            "auto",
            "required",
        ):
            raise ValueError(
                "You can only either use constraints for structured outputs "
                "or tools, not both."
            )
        return data