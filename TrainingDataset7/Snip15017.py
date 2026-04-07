def github_linkcode_resolve(domain, info, *, version, next_version):
    if domain != "py":
        return None

    if not (module := info["module"]):
        return None

    try:
        path, lineno = get_path_and_line(module=module, fullname=info["fullname"])
    except CodeNotFound:
        return None

    branch = get_branch(version=version, next_version=next_version)
    relative_path = path.relative_to(pathlib.Path(__file__).parents[2])
    # Use "/" explicitly to join the path parts since str(file), on Windows,
    # uses the Windows path separator which is incorrect for URLs.
    url_path = "/".join(relative_path.parts)
    return f"https://github.com/django/django/blob/{branch}/{url_path}#L{lineno}"