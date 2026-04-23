def requirements_pre_commit_output() -> str:
    """Generate output for pre-commit dependencies."""
    source = ".pre-commit-config.yaml"
    pre_commit_conf: dict[str, list[dict[str, Any]]]
    pre_commit_conf = load_yaml(source)  # type: ignore[assignment]
    reqs: list[str] = []
    hook: dict[str, Any]
    for repo in (x for x in pre_commit_conf["repos"] if x.get("rev")):
        rev: str = repo["rev"]
        for hook in repo["hooks"]:
            if hook["id"] not in IGNORE_PRE_COMMIT_HOOK_ID:
                pkg = MAP_HOOK_ID_TO_PACKAGE.get(hook["id"]) or hook["id"]
                reqs.append(f"{pkg}=={rev.lstrip('v')}")
                reqs.extend(x for x in hook.get("additional_dependencies", ()))
    output = [
        f"# Automatically generated "
        f"from {source} by {Path(__file__).name}, do not edit",
        "",
    ]
    output.extend(sorted(reqs))
    return "\n".join(output) + "\n"