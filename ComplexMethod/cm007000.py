async def route_to_model(self) -> Message:
        """Main routing method."""
        if not self.models or not self.input_value or not self.judge_llm:
            error_msg = "Missing required inputs: models, input_value, or judge_llm"
            self.status = error_msg
            self.log(f"Validation Error: {error_msg}", "error")
            raise ValueError(error_msg)

        successful_result: Message | None = None
        try:
            self.log(f"Starting model routing with {len(self.models)} available Langflow models.")
            self.log(f"Optimization preference: {self.optimization}")
            self.log(f"Input length: {len(self.input_value)} characters")

            if self.use_openrouter_specs and not self._models_api_cache:
                await self._fetch_openrouter_models_data()

            system_prompt_content = self._create_system_prompt()
            system_message = {"role": "system", "content": system_prompt_content}

            self.status = "Analyzing available models and preparing specifications..."
            model_specs_for_judge = []
            for i, langflow_model_instance in enumerate(self.models):
                langflow_model_name = get_model_name(langflow_model_instance)
                if not langflow_model_name:
                    self.log(f"Warning: Could not determine name for model at index {i}. Using placeholder.", "warning")
                    spec_dict = {
                        "id": f"unknown_model_{i}",
                        "name": f"Unknown Model {i}",
                        "description": "Name could not be determined.",
                    }
                else:
                    spec_dict = self._get_model_specs_dict(langflow_model_name)

                model_specs_for_judge.append({"index": i, "langflow_name": langflow_model_name, "specs": spec_dict})
                self.log(
                    f"Prepared specs for Langflow model {i} ('{langflow_model_name}'): {spec_dict.get('name', 'N/A')}"
                )

            estimated_tokens = len(self.input_value.split()) * 1.3
            self.log(f"Estimated input tokens: {int(estimated_tokens)}")

            query_preview = self.input_value[: self.QUERY_PREVIEW_MAX_LENGTH]
            if len(self.input_value) > self.QUERY_PREVIEW_MAX_LENGTH:
                query_preview += "..."

            user_message_content = f"""User Query: "{query_preview}"
Optimization Preference: {self.optimization}
Estimated Input Tokens: ~{int(estimated_tokens)}

Available Models (JSON list):
{json.dumps(model_specs_for_judge, indent=2)}

Based on the user query, optimization preference, and the detailed model specifications,
select the index of the most appropriate model.
Return ONLY the index number:"""

            user_message = {"role": "user", "content": user_message_content}

            self.log("Requesting model selection from judge LLM...")
            self.status = "Judge LLM analyzing options..."

            response = await self.judge_llm.ainvoke([system_message, user_message])
            self._token_usage = accumulate_usage(self._token_usage, extract_usage_from_message(response))
            selected_index, chosen_model_instance = self._parse_judge_response(response.content.strip())
            self._selected_model_name = get_model_name(chosen_model_instance)
            if self._selected_model_name:
                self._selected_api_model_id = (
                    self._get_api_model_id_for_langflow_model(self._selected_model_name) or self._selected_model_name
                )
            else:
                self._selected_api_model_id = "unknown_model"

            specs_source = (
                "OpenRouter API"
                if self.use_openrouter_specs and self._models_api_cache
                else "Basic (Langflow model names only)"
            )
            self._routing_decision = f"""Model Selection Decision:
- Selected Model Index: {selected_index}
- Selected Langflow Model Name: {self._selected_model_name}
- Selected API Model ID (if resolved): {self._selected_api_model_id}
- Optimization Preference: {self.optimization}
- Input Query Length: {len(self.input_value)} characters (~{int(estimated_tokens)} tokens)
- Number of Models Considered: {len(self.models)}
- Specifications Source: {specs_source}"""

            log_msg = (
                f"DECISION by Judge LLM: Selected model index {selected_index} -> "
                f"Langflow Name: '{self._selected_model_name}', API ID: '{self._selected_api_model_id}'"
            )
            self.log(log_msg)

            self.status = f"Generating response with: {self._selected_model_name}"
            input_message_obj = Message(text=self.input_value)

            raw_result = get_chat_result(
                runnable=chosen_model_instance,
                input_value=input_message_obj,
                token_usage_callback=lambda msg: setattr(
                    self, "_token_usage", accumulate_usage(self._token_usage, extract_usage_from_message(msg))
                ),
            )
            result = Message(text=str(raw_result)) if not isinstance(raw_result, Message) else raw_result

            self.status = f"Successfully routed to: {self._selected_model_name}"
            successful_result = result

        except (ValueError, TypeError, AttributeError, KeyError, RuntimeError) as e:
            error_msg = f"Routing error: {type(e).__name__} - {e!s}"
            self.log(f"{error_msg}", "error")
            self.log("Detailed routing error occurred. Check logs for details.", "error")
            self.status = error_msg

            if self.fallback_to_first and self.models:
                self.log("Activating fallback to first model due to error.", "warning")
                chosen_model_instance = self.models[0]
                self._selected_model_name = get_model_name(chosen_model_instance)
                if self._selected_model_name:
                    mapped_id = self._get_api_model_id_for_langflow_model(self._selected_model_name)
                    self._selected_api_model_id = mapped_id or self._selected_model_name
                else:
                    self._selected_api_model_id = "fallback_model"
                self._routing_decision = f"""Fallback Decision:
- Error During Routing: {error_msg}
- Fallback Model Langflow Name: {self._selected_model_name}
- Fallback Model API ID (if resolved): {self._selected_api_model_id}
- Reason: Automatic fallback enabled"""

                self.status = f"Fallback: Using {self._selected_model_name}"
                input_message_obj = Message(text=self.input_value)

                raw_fallback_result = get_chat_result(
                    runnable=chosen_model_instance,
                    input_value=input_message_obj,
                    token_usage_callback=lambda msg: setattr(
                        self, "_token_usage", accumulate_usage(self._token_usage, extract_usage_from_message(msg))
                    ),
                )
                if not isinstance(raw_fallback_result, Message):
                    successful_result = Message(text=str(raw_fallback_result))
                else:
                    successful_result = raw_fallback_result
            else:
                self.log("No fallback model available or fallback disabled. Raising error.", "error")
                raise

        if successful_result is None:
            error_message = "Unexpected state in route_to_model: No result produced."
            self.log(f"Error: {error_message}", "error")
            raise RuntimeError(error_message)
        return successful_result