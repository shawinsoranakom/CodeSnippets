def get_grouped_models(cls, ignored: list[str] = []) -> dict[str, list[str]]:
        unsorted_models = cls.get_models(ignored=ignored)
        groups = {key: [] for key in LABELS.keys()}

        # Always add default first
        groups["default"].append("default")

        groups["custom"] = list(RouterConfig.routes.keys())

        for model in unsorted_models:
            if model == "default":
                continue  # Already added

            added = False
            # Check for models with prefix
            start = model.split(":")[0]
            if start in ("PollinationsAI", "openrouter"):
                added = True
            # Check for Mistral company models specifically
            elif model.startswith("mistral") and not any(
                x in model for x in ["dolphin", "nous", "openhermes"]
            ):
                groups["mistral"].append(model)
                added = True
            elif (
                model.startswith(
                    ("pixtral-", "ministral-", "codestral", "devstral", "magistral")
                )
                or "mistral" in model
                or "mixtral" in model
            ):
                groups["mistral"].append(model)
                added = True
            # Check for Qwen models
            elif model.startswith(("qwen", "Qwen", "qwq", "qvq")):
                groups["qwen"].append(model)
                added = True
            # Check for Microsoft Phi models
            elif (
                model.startswith(("phi-", "microsoft/")) or "wizardlm" in model.lower()
            ):
                groups["phi"].append(model)
                added = True
            # Check for Meta LLaMA models
            elif model.startswith(("llama-", "meta-llama/", "llama2-", "llama3")):
                groups["llama"].append(model)
                added = True
            elif model == "meta-ai" or model.startswith("codellama-"):
                groups["llama"].append(model)
                added = True
            # Check for Google models
            elif model.startswith(("gemini-", "gemma-", "google/", "bard-")):
                groups["google"].append(model)
                added = True
            # Check for Cohere Command models
            elif model.startswith(("command-", "CohereForAI/", "c4ai-command")):
                groups["command"].append(model)
                added = True
            # Check for DeepSeek models
            elif model.startswith(("deepseek-", "janus-")):
                groups["deepseek"].append(model)
                added = True
            # Check for Perplexity models
            elif model.startswith(("sonar", "sonar-", "pplx-")) or model == "r1-1776":
                groups["perplexity"].append(model)
                added = True
            # Check for image models - UPDATED to include flux check
            elif model in cls.image_models:
                groups["image"].append(model)
                added = True
            # Check for OpenAI models
            elif model.startswith(
                ("gpt-", "chatgpt-", "o1", "o1", "o3", "o4")
            ) or model in ("auto", "searchgpt"):
                groups["openai"].append(model)
                added = True
            # Check for video models
            elif model in cls.video_models:
                groups["video"].append(model)
                added = True
            if not added:
                for group in LABELS.keys():
                    if model == group or group in model:
                        groups[group].append(model)
                        added = True
                        break
            # If not categorized, check for special cases then put in other
            if not added:
                groups["other"].append(model)
        return [
            {"group": LABELS[group], "models": names} for group, names in groups.items()
        ]