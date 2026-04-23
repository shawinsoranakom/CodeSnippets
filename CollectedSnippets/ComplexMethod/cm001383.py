def get_tokenizer(self, model_name: OpenAIModelName) -> ModelTokenizer[int]:
        try:
            return tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback for new models not yet in tiktoken's mapping.
            # GPT-4o, GPT-4.1, GPT-5, O-series use cl100k_base or o200k_base
            if (
                model_name.startswith("gpt-4o")
                or model_name.startswith("gpt-4.1")
                or model_name.startswith("gpt-5")
                or model_name.startswith("o1")
                or model_name.startswith("o3")
                or model_name.startswith("o4")
            ):
                # o200k_base is used by GPT-4o and newer models
                return tiktoken.get_encoding("o200k_base")
            elif model_name.startswith("gpt-4") or model_name.startswith("gpt-3.5"):
                return tiktoken.get_encoding("cl100k_base")
            else:
                # Default fallback
                return tiktoken.get_encoding("cl100k_base")