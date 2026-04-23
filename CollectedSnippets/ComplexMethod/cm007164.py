async def evaluate(self) -> Data:
        if not self.api_key:
            return Data(data={"error": "API key is required"})

        self.set_evaluators(os.getenv("LANGWATCH_ENDPOINT", "https://app.langwatch.ai"))
        self.dynamic_inputs = {}
        if getattr(self, "current_evaluator", None) is None and self.evaluators:
            self.current_evaluator = next(iter(self.evaluators))

        # Prioritize evaluator_name if it exists
        evaluator_name = getattr(self, "evaluator_name", None) or self.current_evaluator

        if not evaluator_name:
            if self.evaluators:
                evaluator_name = next(iter(self.evaluators))
                await logger.ainfo(f"No evaluator was selected. Using default: {evaluator_name}")
            else:
                return Data(
                    data={"error": "No evaluator selected and no evaluators available. Please choose an evaluator."}
                )

        try:
            evaluator = self.evaluators.get(evaluator_name)
            if not evaluator:
                return Data(data={"error": f"Selected evaluator '{evaluator_name}' not found."})

            await logger.ainfo(f"Evaluating with evaluator: {evaluator_name}")

            endpoint = f"/api/evaluations/{evaluator_name}/evaluate"
            url = f"{os.getenv('LANGWATCH_ENDPOINT', 'https://app.langwatch.ai')}{endpoint}"

            headers = {"Content-Type": "application/json", "X-Auth-Token": self.api_key}

            payload = {
                "data": {
                    "input": self.input,
                    "output": self.output,
                    "expected_output": self.expected_output,
                    "contexts": self.contexts.split(",") if self.contexts else [],
                },
                "settings": {},
            }

            if self._tracing_service:
                tracer = self._tracing_service.get_tracer("langwatch")
                if tracer is not None and hasattr(tracer, "trace_id"):
                    payload["settings"]["trace_id"] = str(tracer.trace_id)

            for setting_name in self.dynamic_inputs:
                payload["settings"][setting_name] = getattr(self, setting_name, None)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

            response.raise_for_status()
            result = response.json()

            formatted_result = json.dumps(result, indent=2)
            self.status = f"Evaluation completed successfully. Result:\n{formatted_result}"
            return Data(data=result)

        except (httpx.RequestError, KeyError, AttributeError, ValueError) as e:
            error_message = f"Evaluation error: {e!s}"
            self.status = error_message
            return Data(data={"error": error_message})