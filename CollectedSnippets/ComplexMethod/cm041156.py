def is_canary_settings_update_patch_valid(op: str, path: str) -> bool:
    path_regexes = (
        r"\/canarySettings\/percentTraffic",
        r"\/canarySettings\/deploymentId",
        r"\/canarySettings\/stageVariableOverrides\/.+",
        r"\/canarySettings\/useStageCache",
    )
    if path == "/canarySettings" and op == "remove":
        return True

    matches_path = any(re.match(regex, path) for regex in path_regexes)

    if op not in ("replace", "copy"):
        if matches_path:
            raise BadRequestException(f"Invalid {op} operation with path: {path}")

        raise BadRequestException(
            f"Cannot {op} method setting {path.lstrip('/')} because there is no method setting for this method "
        )

    # stageVariableOverrides is a bit special as it's nested, it doesn't return the same error message
    if not matches_path and path != "/canarySettings/stageVariableOverrides":
        return False

    return True