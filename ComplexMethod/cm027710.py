def validate_manifest(integration: Integration, core_components_dir: Path) -> None:
    """Validate manifest."""
    try:
        if integration.core:
            manifest_schema(integration.manifest)
        else:
            CUSTOM_INTEGRATION_MANIFEST_SCHEMA(integration.manifest)
    except vol.Invalid as err:
        integration.add_error(
            "manifest", f"Invalid manifest: {humanize_error(integration.manifest, err)}"
        )

    if (domain := integration.manifest["domain"]) != integration.path.name:
        integration.add_error("manifest", "Domain does not match dir name")

    if not integration.core and (core_components_dir / domain).exists():
        integration.add_warning(
            "manifest", "Domain collides with built-in core integration"
        )

    if domain in NO_IOT_CLASS and "iot_class" in integration.manifest:
        integration.add_error("manifest", "Domain should not have an IoT Class")

    if (
        domain not in NO_IOT_CLASS
        and "iot_class" not in integration.manifest
        and integration.integration_type != IntegrationType.VIRTUAL
    ):
        integration.add_error("manifest", "Domain is missing an IoT Class")

    if (
        integration.integration_type == IntegrationType.VIRTUAL
        and (supported_by := integration.manifest.get("supported_by"))
        and not (core_components_dir / supported_by).exists()
    ):
        integration.add_error(
            "manifest",
            "Virtual integration points to non-existing supported_by integration",
        )

    if (
        (quality_scale := integration.manifest.get("quality_scale"))
        and quality_scale.upper() in ScaledQualityScaleTiers
        and ScaledQualityScaleTiers[quality_scale.upper()]
        >= ScaledQualityScaleTiers.SILVER
    ):
        if not integration.manifest.get("codeowners"):
            integration.add_error(
                "manifest",
                f"{quality_scale} integration does not have a code owner",
            )

    if not integration.core:
        validate_version(integration)