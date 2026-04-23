def _run_validation(self):
        """Run validation once and store the result."""
        # If validation already ran, return the cached result
        if self._validation_result is not None:
            return self._validation_result

        # Initialize failed checks list
        self._failed_checks = []

        # Get LLM using unified model system
        llm = None
        if hasattr(self, "model") and self.model:
            try:
                llm = get_llm(model=self.model, user_id=self.user_id, api_key=self.api_key)
            except (ValueError, TypeError, RuntimeError, KeyError, AttributeError) as e:
                error_msg = f"Error initializing LLM: {e!s}"
                self.status = f"ERROR: {error_msg}"
                self._validation_result = False
                self._failed_checks.append(f"LLM Configuration: {error_msg}")
                raise

        # Validate LLM is provided and usable
        if not llm:
            error_msg = "No LLM provided for validation"
            self.status = f"ERROR: {error_msg}"
            self._validation_result = False
            self._failed_checks.append("LLM Configuration: No model selected. Please select a Language Model.")
            raise ValueError(error_msg)

        # Check if LLM has required methods
        if not (hasattr(llm, "invoke") or callable(llm)):
            error_msg = "Invalid LLM configuration - LLM is not properly configured"
            self.status = f"ERROR: {error_msg}"
            self._validation_result = False
            self._failed_checks.append(
                "LLM Configuration: LLM is not properly configured. Please verify your model configuration."
            )
            raise ValueError(error_msg)

        # Run all enabled checks (fail fast - stop on first failure)
        all_passed = True
        self._failed_checks = []

        for check_name, check_desc in self._checks_to_run:
            self.status = f"Checking {check_name}..."
            passed, _reason = self._check_guardrail(llm, self._extracted_text, check_name, check_desc)

            if not passed:
                all_passed = False
                # Use fixed justification for each check type
                fixed_justification = self._get_fixed_justification(check_name)
                self._failed_checks.append(f"{check_name}: {fixed_justification}")
                self.status = f"FAILED: {check_name} check failed: {fixed_justification}"
                # Fail fast: stop checking remaining validators when one fails
                break

        # Store result
        self._validation_result = all_passed

        if all_passed:
            self.status = f"OK: All {len(self._checks_to_run)} guardrail checks passed"
        else:
            failure_summary = "\n".join(self._failed_checks)
            checks_run = len(self._failed_checks)
            checks_skipped = len(self._checks_to_run) - checks_run
            if checks_skipped > 0:
                self.status = (
                    f"FAILED: Guardrail validation failed (stopped early after {checks_run} "
                    f"check(s), skipped {checks_skipped}):\n{failure_summary}"
                )
            else:
                self.status = f"FAILED: Guardrail validation failed:\n{failure_summary}"

        return all_passed