def _create_chat_result(
        self,
        response: dict | openai.BaseModel,
        generation_info: dict | None = None,
    ) -> ChatResult:
        chat_result = super()._create_chat_result(response, generation_info)

        if not isinstance(response, dict):
            response = response.model_dump()
        for res in response["choices"]:
            if res.get("finish_reason", None) == "content_filter":
                msg = (
                    "Azure has not provided the response due to a content filter "
                    "being triggered"
                )
                raise ValueError(msg)

        if "model" in response:
            model = response["model"]
            if self.model_version:
                model = f"{model}-{self.model_version}"

            chat_result.llm_output = chat_result.llm_output or {}
            chat_result.llm_output["model_name"] = model
        if "prompt_filter_results" in response:
            chat_result.llm_output = chat_result.llm_output or {}
            chat_result.llm_output["prompt_filter_results"] = response[
                "prompt_filter_results"
            ]
        for chat_gen, response_choice in zip(
            chat_result.generations, response["choices"], strict=False
        ):
            chat_gen.generation_info = chat_gen.generation_info or {}
            chat_gen.generation_info["content_filter_results"] = response_choice.get(
                "content_filter_results", {}
            )

        return chat_result