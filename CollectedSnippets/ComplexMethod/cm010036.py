def _parse_repo_info(github):
    if ":" in github:
        repo_info, ref = github.split(":")
    else:
        repo_info, ref = github, None
    repo_owner, repo_name = repo_info.split("/")

    if ref is None:
        # The ref wasn't specified by the user, so we need to figure out the
        # default branch: main or master. Our assumption is that if main exists
        # then it's the default branch, otherwise it's master.
        try:
            with urlopen(f"https://github.com/{repo_owner}/{repo_name}/tree/main/"):
                ref = "main"
        except HTTPError as e:
            if e.code == 404:
                ref = "master"
            else:
                raise
        except URLError as e:
            # No internet connection, need to check for cache as last resort
            for possible_ref in ("main", "master"):
                if os.path.exists(
                    f"{get_dir()}/{repo_owner}_{repo_name}_{possible_ref}"
                ):
                    ref = possible_ref
                    break
            if ref is None:
                raise RuntimeError(
                    "It looks like there is no internet connection and the "
                    f"repo could not be found in the cache ({get_dir()})"
                ) from e
    return repo_owner, repo_name, ref