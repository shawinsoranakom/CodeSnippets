def _load_disabled_vllm_tests_from_yaml() -> list[dict[str, Any]]:
    if not _DISABLED_VLLM_TESTS_PATH.exists():
        return []
    with open(_DISABLED_VLLM_TESTS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "disabled_tests" not in data:
        return []
    entries = data["disabled_tests"]
    if not entries:
        return []
    for entry in entries:
        if "test" not in entry or "issue" not in entry:
            raise ValueError(
                f"disabled_vllm_tests.yaml: each entry must have 'test' and 'issue' keys, got {entry}"
            )
    return entries