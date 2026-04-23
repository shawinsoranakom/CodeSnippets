def check(commit: _Commit, force_unsafe: bool = False):
    next_version = None
    reason = ""
    # Step 1: Detect major schema updates.
    if len(commit.additions) > 0:
        for k, v in commit.additions.items():
            if k not in commit.base:
                continue
            kind = commit.result[k]["kind"]
            fields = v["fields"]
            for f, d in fields.items():
                if kind == "struct" and "default" not in d:
                    reason += (
                        f"Field {k}.{f} is added to schema.py without a default value as an incompatible change "
                        + "which requires major version bump.\n"
                    )
                    next_version = [commit.base["SCHEMA_VERSION"][0] + 1, 1]

    if len(commit.subtractions) > 0:
        for k, v in commit.subtractions.items():
            if k not in commit.result:
                continue
            for f in v["fields"]:
                reason = f"Field {k}.{f} is removed from schema.py as an incompatible change which requires major version bump.\n"
            next_version = [commit.base["SCHEMA_VERSION"][0] + 1, 1]

    if force_unsafe:
        reason += "--force-unsafe is used."
        next_version = commit.result["SCHEMA_VERSION"]
    else:
        # Step 2: Detect minor schema updates.
        if next_version is None and len(commit.additions) > 0:
            for k, v in commit.additions.items():
                for f in v["fields"]:
                    reason += (
                        f"Field {k}.{f} is added to schema.py as an compatible change "
                        + "which still requires minor version bump.\n"
                    )
            next_version = [
                commit.base["SCHEMA_VERSION"][0],
                commit.base["SCHEMA_VERSION"][1] + 1,
            ]
        if next_version is None and len(commit.subtractions) > 0:
            for k, v in commit.subtractions.items():
                for f in v["fields"]:
                    reason += (
                        f"Field {k}.{f} is removed from schema.py as an compatible change "
                        + "which still requires minor version bump.\n"
                    )
            next_version = [
                commit.base["SCHEMA_VERSION"][0],
                commit.base["SCHEMA_VERSION"][1] + 1,
            ]

    return next_version, reason