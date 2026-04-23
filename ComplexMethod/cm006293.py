def _walk_steps(steps: list[dict[str, Any]]) -> None:
            nonlocal total_prompt_tokens, total_completion_tokens, total_tokens
            nonlocal total_cost, model, provider, model_parameters

            for step in steps:
                if step.get("type") == "chat_completion":
                    total_prompt_tokens += step.get("promptTokens") or 0
                    total_completion_tokens += step.get("completionTokens") or 0
                    total_tokens += step.get("tokens") or 0
                    total_cost += step.get("cost") or 0.0

                    # Capture model info from the first ChatCompletionStep
                    if model is None and step.get("model"):
                        model = step["model"]
                    if provider is None and step.get("provider"):
                        provider = step["provider"]
                    if model_parameters is None and step.get("modelParameters"):
                        model_parameters = step["modelParameters"]

                # Recurse into nested steps
                nested = step.get("steps")
                if nested:
                    _walk_steps(nested)