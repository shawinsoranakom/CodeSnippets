def _combine_llm_outputs(self, llm_outputs: list[dict | None]) -> dict:
        overall_token_usage: dict = {}
        system_fingerprint = None
        for output in llm_outputs:
            if output is None:
                # Happens in streaming
                continue
            token_usage = output["token_usage"]
            if token_usage is not None:
                for k, v in token_usage.items():
                    if k in overall_token_usage and v is not None:
                        # Handle nested dictionaries
                        if isinstance(v, dict):
                            if k not in overall_token_usage:
                                overall_token_usage[k] = {}
                            for nested_k, nested_v in v.items():
                                if (
                                    nested_k in overall_token_usage[k]
                                    and nested_v is not None
                                ):
                                    overall_token_usage[k][nested_k] += nested_v
                                else:
                                    overall_token_usage[k][nested_k] = nested_v
                        else:
                            overall_token_usage[k] += v
                    else:
                        overall_token_usage[k] = v
            if system_fingerprint is None:
                system_fingerprint = output.get("system_fingerprint")
        combined = {"token_usage": overall_token_usage, "model_name": self.model_name}
        if system_fingerprint:
            combined["system_fingerprint"] = system_fingerprint
        if self.service_tier:
            combined["service_tier"] = self.service_tier
        return combined