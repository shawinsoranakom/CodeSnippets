def print_image_models():
    lines = [
        "| Label | Provider | Image Model | Vision Model | Website |",
        "| ----- | -------- | ----------- | ------------ | ------- |",
    ]
    for provider in [provider for provider in __providers__ if provider.working and getattr(provider, "image_models", None) or getattr(provider, "vision_models", None)]:
        provider_url = provider.url if provider.url else "❌"
        netloc = urlparse(provider_url).netloc.replace("www.", "")
        website = f"[{netloc}]({provider_url})"
        label = getattr(provider, "label", provider.__name__)
        if provider.image_models:
            image_models = ", ".join([model for model in provider.image_models if model in _all_models])
        else:
            image_models = "❌"
        if hasattr(provider, "vision_models"):
            vision_models = "✔️"
        else:
            vision_models = "❌"
        lines.append(f'| {label} | `g4f.Provider.{provider.__name__}` | {image_models}| {vision_models} | {website} |')

    return lines