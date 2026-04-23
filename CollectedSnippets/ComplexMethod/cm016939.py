def calculate_tokens_price(response: GeminiGenerateContentResponse) -> float | None:
    if not response.modelVersion:
        return None
    # Define prices (Cost per 1,000,000 tokens), see https://cloud.google.com/vertex-ai/generative-ai/pricing
    if response.modelVersion in ("gemini-2.5-pro-preview-05-06", "gemini-2.5-pro"):
        input_tokens_price = 1.25
        output_text_tokens_price = 10.0
        output_image_tokens_price = 0.0
    elif response.modelVersion in (
        "gemini-2.5-flash-preview-04-17",
        "gemini-2.5-flash",
    ):
        input_tokens_price = 0.30
        output_text_tokens_price = 2.50
        output_image_tokens_price = 0.0
    elif response.modelVersion in (
        "gemini-2.5-flash-image-preview",
        "gemini-2.5-flash-image",
    ):
        input_tokens_price = 0.30
        output_text_tokens_price = 2.50
        output_image_tokens_price = 30.0
    elif response.modelVersion in ("gemini-3-pro-preview", "gemini-3.1-pro-preview"):
        input_tokens_price = 2
        output_text_tokens_price = 12.0
        output_image_tokens_price = 0.0
    elif response.modelVersion == "gemini-3.1-flash-lite-preview":
        input_tokens_price = 0.25
        output_text_tokens_price = 1.50
        output_image_tokens_price = 0.0
    elif response.modelVersion == "gemini-3-pro-image-preview":
        input_tokens_price = 2
        output_text_tokens_price = 12.0
        output_image_tokens_price = 120.0
    elif response.modelVersion == "gemini-3.1-flash-image-preview":
        input_tokens_price = 0.5
        output_text_tokens_price = 3.0
        output_image_tokens_price = 60.0
    else:
        return None
    final_price = response.usageMetadata.promptTokenCount * input_tokens_price
    if response.usageMetadata.candidatesTokensDetails:
        for i in response.usageMetadata.candidatesTokensDetails:
            if i.modality == Modality.IMAGE:
                final_price += output_image_tokens_price * i.tokenCount  # for Nano Banana models
            else:
                final_price += output_text_tokens_price * i.tokenCount
    if response.usageMetadata.thoughtsTokenCount:
        final_price += output_text_tokens_price * response.usageMetadata.thoughtsTokenCount
    return final_price / 1_000_000.0