def _merge_criteria_processor_list(
        self,
        default_list: LogitsProcessorList | StoppingCriteriaList,
        custom_list: LogitsProcessorList | StoppingCriteriaList,
    ) -> LogitsProcessorList | StoppingCriteriaList:
        """
        Merge user-defined processors/criteria with the ones instantiated inside `generate`. In case the same
        processor/criteria is present on both lists, use the user-defined one.

        (Note: up to v4.49.0, this function threw an exception is the same logit processor was found twice.)
        """
        if len(custom_list) == 0:
            return default_list

        final_list = type(default_list)()
        for default in default_list:
            using_custom = False
            for custom in custom_list:
                if type(custom) is type(default):
                    object_type = "stopping criteria" if isinstance(custom, StoppingCriteria) else "logits processor"
                    logger.warning_once(
                        f"A custom {object_type} of type {type(custom)} has been passed to `.generate()`, but it "
                        f"was also created in `.generate()`, given its parameterization. The custom {type(custom)} "
                        f"will take precedence. Please check the docstring of {type(custom)} to see related "
                        "`.generate()` flags."
                    )
                    final_list.append(custom)
                    using_custom = True
                    break
            if not using_custom:
                final_list.append(default)

        for custom in custom_list:
            if custom not in final_list:
                final_list.append(custom)
        return final_list