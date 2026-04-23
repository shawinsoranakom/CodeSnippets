def _filter_jobs(
    test_matrix: dict[str, list[Any]],
    issue_type: IssueType,
    target_cfg: str | None = None,
) -> dict[str, list[Any]]:
    """
    An utility function used to actually apply the job filter
    """
    # The result will be stored here
    filtered_test_matrix: dict[str, list[Any]] = {"include": []}

    # This is an issue to disable a CI job
    if issue_type == IssueType.DISABLED:
        # If there is a target config, disable (remove) only that
        if target_cfg:
            # Remove the target config from the test matrix
            filtered_test_matrix["include"] = [
                r for r in test_matrix["include"] if r.get("config", "") != target_cfg
            ]

        return filtered_test_matrix

    if issue_type == IssueType.UNSTABLE:
        for r in test_matrix["include"]:
            cpy = r.copy()

            if (target_cfg and r.get("config", "") == target_cfg) or not target_cfg:
                # If there is a target config, only mark that as unstable, otherwise,
                # mark everything as unstable
                cpy[IssueType.UNSTABLE.value] = IssueType.UNSTABLE.value

            filtered_test_matrix["include"].append(cpy)

        return filtered_test_matrix

    # No matching issue, return everything
    return test_matrix