def _pre_run_setup(self):
        """Reset validation state before each run."""
        self._validation_result: bool | None = None
        self._failed_checks = []

        """Validate inputs before each run."""
        input_text_value = getattr(self, "input_text", "")
        input_text = self._extract_text(input_text_value)
        if not input_text or not input_text.strip():
            error_msg = "Input text is empty. Please provide valid text for guardrail validation."
            self.status = f"ERROR: {error_msg}"
            self._failed_checks.append(
                "Input Validation: Input text is empty. Please provide valid text for guardrail validation."
            )
            raise ValueError(error_msg)

        self._extracted_text = input_text

        enabled_names = getattr(self, "enabled_guardrails", [])
        if not isinstance(enabled_names, list):
            enabled_names = []

        if getattr(self, "enable_custom_guardrail", False):
            custom_explanation = getattr(self, "custom_guardrail_explanation", "")
            if custom_explanation and str(custom_explanation).strip():
                enabled_names.append("Custom Guardrail")
                guardrail_descriptions["Custom Guardrail"] = str(custom_explanation).strip()

        if not enabled_names:
            error_msg = "No guardrails enabled. Please select at least one guardrail to validate."
            self.status = f"ERROR: {error_msg}"
            self._failed_checks.append("Configuration: No guardrails selected for validation")
            raise ValueError(error_msg)

        enabled_guardrails = [str(item) for item in enabled_names if item]

        self._checks_to_run = [
            (name, guardrail_descriptions[name]) for name in enabled_guardrails if name in guardrail_descriptions
        ]