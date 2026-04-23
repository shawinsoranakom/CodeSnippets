def _create_chat_result(
        self, response: dict | BaseModel, params: dict
    ) -> ChatResult:
        generations = []
        if not isinstance(response, dict):
            response = response.model_dump()
        token_usage = response.get("usage", {})
        for res in response["choices"]:
            message = _convert_dict_to_message(res["message"])
            if token_usage and isinstance(message, AIMessage):
                message.usage_metadata = _create_usage_metadata(token_usage)
            generation_info = {"finish_reason": res.get("finish_reason")}
            if "logprobs" in res:
                generation_info["logprobs"] = res["logprobs"]
            gen = ChatGeneration(
                message=message,
                generation_info=generation_info,
            )
            generations.append(gen)
        llm_output = {
            "token_usage": token_usage,
            "model_name": self.model_name,
            "system_fingerprint": response.get("system_fingerprint", ""),
        }
        llm_output["service_tier"] = params.get("service_tier") or self.service_tier
        reasoning_effort = params.get("reasoning_effort") or self.reasoning_effort
        if reasoning_effort:
            llm_output["reasoning_effort"] = reasoning_effort
        return ChatResult(generations=generations, llm_output=llm_output)