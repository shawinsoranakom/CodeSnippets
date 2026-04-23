def _check_version_mismatch(flow: dict[str, Any], result: ValidationResult) -> None:
    """Warn when nodes were built with a different Langflow version.

    Each unique ``lf_version`` embedded in the node metadata that differs from
    the currently installed Langflow version triggers a single warning covering
    all affected nodes.  If Langflow is not installed the check is skipped
    silently (lfx can run standalone).
    """
    from lfx.cli.validation.core import _get_lf_version

    installed = _get_lf_version()
    if installed is None:
        return  # Langflow not installed; skip silently

    nodes: list[dict[str, Any]] = [n for n in flow.get("data", {}).get("nodes", []) if isinstance(n, dict)]

    # Collect node IDs grouped by the version they were built with
    version_to_nodes: dict[str, list[str]] = {}
    for node in nodes:
        lf_version: str | None = node.get("data", {}).get("node", {}).get("lf_version")
        if lf_version and lf_version != installed:
            version_to_nodes.setdefault(lf_version, []).append(_node_display_name(node) or node.get("id") or "?")

    _max_sample = 3
    for built_version, node_names in sorted(version_to_nodes.items()):
        count = len(node_names)
        sample = ", ".join(node_names[:_max_sample]) + (" ..." if count > _max_sample else "")
        result.issues.append(
            _make_issue(
                level=_LEVEL_STRUCTURAL,
                severity="warning",
                node_id=None,
                node_name=None,
                message=(
                    f"{count} component(s) built with Langflow {built_version} "
                    f"(installed: {installed}) -- re-export recommended. "
                    f"Affected: {sample}"
                ),
            )
        )