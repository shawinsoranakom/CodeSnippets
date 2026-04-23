def tp_plan(self, plan: dict[str, str] | None):
        if plan is None:
            self._tp_plan = {}
            return
        if not isinstance(plan, dict):
            raise ValueError("Can only set a dictionary as `tp_plan`")

        # Ensure the styles are all valid
        for layer_pattern, parallel_style in plan.items():
            if parallel_style not in ALL_PARALLEL_STYLES:
                raise ValueError(
                    f"Unsupported tensor parallel style '{parallel_style}' for layer '{layer_pattern}'. "
                    f"Supported styles are {list(ALL_PARALLEL_STYLES.keys())}"
                )

        # Validate that the layer patterns match existing model structure. We check this by getting all parameter
        # names and seeing if any match the patterns
        model_param_names = [name for name, _ in self.named_parameters()]
        for layer_pattern in plan.keys():
            # Convert pattern to regex (replace * with .*)
            regex_pattern = layer_pattern.replace("*", r"\d+")
            pattern_matched = False
            for param_name in model_param_names:
                if re.match(regex_pattern, param_name):
                    pattern_matched = True
                    break
            if not pattern_matched:
                warnings.warn(
                    f"Layer pattern '{layer_pattern}' does not match any parameters in the model. This rule may not "
                    "be applied during tensor parallelization, or may lead to dimension mismatches"
                )

        # Set the plan
        self._tp_plan = plan