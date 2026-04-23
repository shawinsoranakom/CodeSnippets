def generate_and_validate(integrations: dict[str, Integration]) -> str:
    """Validate and generate lab preview features data."""
    labs_dict: dict[str, dict[str, dict[str, str]]] = {}

    for domain in sorted(integrations):
        integration = integrations[domain]
        preview_features = integration.manifest.get("preview_features")

        if not preview_features:
            continue

        if not isinstance(preview_features, dict):
            integration.add_error(
                "labs",
                f"preview_features must be a dict, got {type(preview_features).__name__}",
            )
            continue

        # Extract features with full data
        domain_preview_features: dict[str, dict[str, str]] = {}
        for preview_feature_id, preview_feature_config in preview_features.items():
            if not isinstance(preview_feature_id, str):
                integration.add_error(
                    "labs",
                    f"preview_features keys must be strings, got {type(preview_feature_id).__name__}",
                )
                break
            if not isinstance(preview_feature_config, dict):
                integration.add_error(
                    "labs",
                    f"preview_features[{preview_feature_id}] must be a dict, got {type(preview_feature_config).__name__}",
                )
                break
            # Include the full feature configuration
            domain_preview_features[preview_feature_id] = {
                "feedback_url": preview_feature_config.get("feedback_url", ""),
                "learn_more_url": preview_feature_config.get("learn_more_url", ""),
                "report_issue_url": preview_feature_config.get("report_issue_url", ""),
            }
        else:
            # Only add if all features are valid
            if domain_preview_features:
                labs_dict[domain] = domain_preview_features

    return format_python_namespace(
        {
            "LABS_PREVIEW_FEATURES": labs_dict,
        }
    )