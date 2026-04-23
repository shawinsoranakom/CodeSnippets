def _evaluate_once(self):
        if not hasattr(self, "_cached_result"):
            try:
                self.status = "Configuring selected evals..."
                default_evals = get_default_evals()
                enabled_names = []
                if self.run_context_sufficiency:
                    enabled_names.append("context_sufficiency")
                if self.run_response_groundedness:
                    enabled_names.append("response_groundedness")
                if self.run_response_helpfulness:
                    enabled_names.append("response_helpfulness")
                if self.run_query_ease:
                    enabled_names.append("query_ease")

                selected_evals = [e for e in default_evals if e.name in enabled_names]

                validator = TrustworthyRAG(
                    api_key=self.api_key,
                    quality_preset=self.quality_preset,
                    options={"log": ["explanation"], "model": self.model},
                    evals=selected_evals,
                )

                self.status = f"Running evals: {[e.name for e in selected_evals]}"
                self._cached_result = validator.score(
                    query=self.query,
                    context=self.context,
                    response=self.response,
                )
                self.status = "Evaluation complete."

            except Exception as e:  # noqa: BLE001
                self.status = f"Evaluation failed: {e!s}"
                self._cached_result = {}
        return self._cached_result