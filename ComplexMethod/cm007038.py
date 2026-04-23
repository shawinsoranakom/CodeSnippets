def model_select(self) -> Message:
        api_key = SecretStr(self.api_key).get_secret_value() if self.api_key else None
        input_value = self.input_value
        system_message = self.system_message
        messages = self._format_input(input_value, system_message)

        selected_models = []
        mapped_selected_models = []
        for model in self.models:
            model_name = get_model_name(model)

            if model_name in ND_MODEL_MAPPING:
                selected_models.append(model)
                mapped_selected_models.append(ND_MODEL_MAPPING[model_name])

        payload = {
            "messages": messages,
            "llm_providers": mapped_selected_models,
            "hash_content": self.hash_content,
        }

        if self.tradeoff != "quality":
            payload["tradeoff"] = self.tradeoff

        if self.preference_id and self.preference_id != "":
            payload["preference_id"] = self.preference_id

        header = {
            "Authorization": f"Bearer {api_key}",
            "accept": "application/json",
            "content-type": "application/json",
        }

        response = requests.post(
            "https://api.notdiamond.ai/v2/modelRouter/modelSelect",
            json=payload,
            headers=header,
            timeout=10,
        )

        result = response.json()
        chosen_model = self.models[0]  # By default there is a fallback model
        self._selected_model_name = get_model_name(chosen_model)

        if "providers" not in result:
            # No provider returned by NotDiamond API, likely failed. Fallback to first model.
            return self._call_get_chat_result(chosen_model, input_value, system_message)

        providers = result["providers"]

        if len(providers) == 0:
            # No provider returned by NotDiamond API, likely failed. Fallback to first model.
            return self._call_get_chat_result(chosen_model, input_value, system_message)

        nd_result = providers[0]

        for nd_model, selected_model in zip(mapped_selected_models, selected_models, strict=False):
            if nd_model["provider"] == nd_result["provider"] and nd_model["model"] == nd_result["model"]:
                chosen_model = selected_model
                self._selected_model_name = get_model_name(chosen_model)
                break

        return self._call_get_chat_result(chosen_model, input_value, system_message)