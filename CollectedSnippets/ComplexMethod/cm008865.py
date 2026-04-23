def _get_configs_for_multi_dirs(
    job: str, dirs_to_run: Dict[str, Set[str]], dependents: dict
) -> List[Dict[str, str]]:
    if job == "lint":
        dirs = add_dependents(
            dirs_to_run["lint"] | dirs_to_run["test"] | dirs_to_run["extended-test"],
            dependents,
        )
    elif job in ["test", "compile-integration-tests", "dependencies", "test-pydantic"]:
        dirs = add_dependents(
            dirs_to_run["test"] | dirs_to_run["extended-test"], dependents
        )
    elif job == "extended-tests":
        dirs = list(dirs_to_run["extended-test"])
    elif job == "codspeed":
        dirs = list(dirs_to_run["codspeed"])
    elif job == "vcr-tests":
        # Only run VCR tests for packages that have cassettes and are affected
        all_affected = set(
            add_dependents(
                dirs_to_run["test"] | dirs_to_run["extended-test"], dependents
            )
        )
        dirs = [d for d in VCR_PACKAGES if d in all_affected]
    else:
        raise ValueError(f"Unknown job: {job}")

    return [
        config for dir_ in dirs for config in _get_configs_for_single_dir(job, dir_)
    ]