def print_providers():
    providers = [provider for provider in __providers__ if provider.working]
    responses = test_async_list(providers)
    lines = []
    for type in ("Free", "Auth"):
        lines += [
            "",
            f"## {type}",
            "",
        ]
        for idx, _provider in enumerate(providers):
            do_continue = False
            if type == "Auth" and _provider.needs_auth:
                do_continue = True
            elif type == "Free" and not _provider.needs_auth:
                do_continue = True
            if not do_continue:
                continue

            lines.append(
                f"### {getattr(_provider, 'label', _provider.__name__)}",
            )
            provider_name = f"`g4f.Provider.{_provider.__name__}`"
            lines.append(f"| Provider | {provider_name} |")
            lines.append("| -------- | ---- |")

            if _provider.url:
                netloc = urlparse(_provider.url).netloc.replace("www.", "")
                website = f"[{netloc}]({_provider.url})"
            else:
                website = "❌"

            message_history = "✔️" if _provider.supports_message_history else "❌"
            system = "✔️" if _provider.supports_system_message else "❌"
            stream = "✔️" if _provider.supports_stream else "❌"
            if _provider.working:
                status = '![Active](https://img.shields.io/badge/Active-brightgreen)'
                if responses[idx]:
                    status = '![Active](https://img.shields.io/badge/Active-brightgreen)'
                else:
                    status = '![Unknown](https://img.shields.io/badge/Unknown-grey)'
            else:
                status = '![Inactive](https://img.shields.io/badge/Inactive-red)'
            auth = "✔️" if _provider.needs_auth else "❌"

            lines.append(f"| **Website** | {website} | \n| **Status** | {status} |")

            if issubclass(_provider, ProviderModelMixin):
                try:
                    all_models = _provider.get_models()
                    models = [model for model in _all_models if model in all_models or model in _provider.model_aliases]
                    image_models = _provider.image_models
                    if image_models:
                        for alias, name in _provider.model_aliases.items():
                            if alias in _all_models and name in image_models:
                                image_models.append(alias)
                        image_models = [model for model in image_models if model in _all_models]
                        if image_models:
                            models = [model for model in models if model not in image_models]
                    if models:
                        lines.append(f"| **Models** | {', '.join(models)} ({len(all_models)})|")
                    if image_models:
                        lines.append(f"| **Image Models (Image Generation)** | {', '.join(image_models)} |")
                    if hasattr(_provider, "vision_models"):
                        lines.append(f"| **Vision (Image Upload)** | ✔️ |")
                except Exception:
                    pass

            lines.append(f"| **Authentication** | {auth} | \n| **Streaming** | {stream} |")
            lines.append(f"| **System message** | {system} | \n| **Message history** | {message_history} |")
    return lines