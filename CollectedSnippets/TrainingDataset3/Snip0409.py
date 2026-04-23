async def get_execution_analytics_config(
    admin_user_id: str = Security(get_user_id),
):
    """
    Get the configuration for execution analytics including:
    - Available AI models with metadata
    - Default system and user prompts
    - Recommended model selection
    """
    logger.info(f"Admin user {admin_user_id} requesting execution analytics config")

    # Generate model list from LlmModel enum with provider information
    available_models = []

    # Function to generate friendly display names from model values
    def generate_model_label(model: LlmModel) -> str:
        """Generate a user-friendly label from the model enum value."""
        value = model.value

        # For all models, convert underscores/hyphens to spaces and title case
        # e.g., "gpt-4-turbo" -> "GPT 4 Turbo", "claude-3-haiku-20240307" -> "Claude 3 Haiku"
        parts = value.replace("_", "-").split("-")

        # Handle provider prefixes (e.g., "google/", "x-ai/")
        if "/" in value:
            _, model_name = value.split("/", 1)
            parts = model_name.replace("_", "-").split("-")

        # Capitalize and format parts
        formatted_parts = []
        for part in parts:
            # Skip date-like patterns - check for various date formats:
            # - Long dates like "20240307" (8 digits)
            # - Year components like "2024", "2025" (4 digit years >= 2020)
            # - Month/day components like "04", "16" when they appear to be dates
            if part.isdigit():
                if len(part) >= 8:  # Long date format like "20240307"
                    continue
                elif len(part) == 4 and int(part) >= 2020:  # Year like "2024", "2025"
                    continue
                elif len(part) <= 2 and int(part) <= 31:  # Month/day like "04", "16"
                    # Skip if this looks like a date component (basic heuristic)
                    continue
            # Keep version numbers as-is
            if part.replace(".", "").isdigit():
                formatted_parts.append(part)
            # Capitalize normal words
            else:
                formatted_parts.append(
                    part.upper()
                    if part.upper() in ["GPT", "LLM", "API", "V0"]
                    else part.capitalize()
                )

        model_name = " ".join(formatted_parts)

        # Format provider name for better display
        provider_name = model.provider.replace("_", " ").title()

        # Return with provider prefix for clarity
        return f"{provider_name}: {model_name}"

    # Include all LlmModel values (no more filtering by hardcoded list)
    recommended_model = LlmModel.GPT4O_MINI.value
    for model in LlmModel:
        label = generate_model_label(model)
        # Add "(Recommended)" suffix to the recommended model
        if model.value == recommended_model:
            label += " (Recommended)"

        available_models.append(
            ModelInfo(
                value=model.value,
                label=label,
                provider=model.provider,
            )
        )

    # Sort models by provider and name for better UX
    available_models.sort(key=lambda x: (x.provider, x.label))

    return ExecutionAnalyticsConfig(
        available_models=available_models,
        default_system_prompt=DEFAULT_SYSTEM_PROMPT,
        default_user_prompt=DEFAULT_USER_PROMPT,
        recommended_model=recommended_model,
    )
