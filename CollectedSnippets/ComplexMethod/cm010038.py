def _check_repo_is_trusted(
    repo_owner,
    repo_name,
    owner_name_branch,
    trust_repo,
):
    hub_dir = get_dir()
    filepath = os.path.join(hub_dir, "trusted_list")

    if not os.path.exists(filepath):
        Path(filepath).touch()
    with open(filepath) as file:
        trusted_repos = tuple(line.strip() for line in file)

    # To minimize friction of introducing the new trust_repo mechanism, we consider that
    # if a repo was already downloaded by torchhub, then it is already trusted (even if it's not in the allowlist)
    trusted_repos_legacy = next(os.walk(hub_dir))[1]

    owner_name = "_".join([repo_owner, repo_name])
    is_trusted = (
        owner_name in trusted_repos
        or owner_name_branch in trusted_repos_legacy
        or repo_owner in _TRUSTED_REPO_OWNERS
    )

    if (trust_repo is False) or (trust_repo == "check" and not is_trusted):
        response = input(
            f"The repository {owner_name} does not belong to the list of trusted repositories and as such cannot be downloaded. "
            "Do you trust this repository and wish to add it to the trusted list of repositories (y/N)?"
        )
        if response.lower() in ("y", "yes"):
            if is_trusted:
                print("The repository is already trusted.")
        elif response.lower() in ("n", "no", ""):
            raise Exception("Untrusted repository.")  # noqa: TRY002
        else:
            raise ValueError(f"Unrecognized response {response}.")

    # At this point we're sure that the user trusts the repo (or wants to trust it)
    if not is_trusted:
        with open(filepath, "a") as file:
            file.write(owner_name + "\n")