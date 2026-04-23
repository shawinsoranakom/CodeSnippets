def check_python_external_dependency(pydep: str) -> None:
    try:
        requirement = Requirement(pydep)
    except InvalidRequirement as e:
        msg = f"{pydep} is an invalid external dependency specification: {e}"
        raise ValueError(msg) from e
    if requirement.marker and not requirement.marker.evaluate():
        _logger.debug(
            "Ignored external dependency %s because environment markers do not match",
            pydep
        )
        return
    try:
        version = importlib.metadata.version(requirement.name)
    except importlib.metadata.PackageNotFoundError as e:
        try:
            # keep compatibility with module name but log a warning instead of info
            importlib.import_module(pydep)
            _logger.warning("python external dependency on '%s' does not appear o be a valid PyPI package. Using a PyPI package name is recommended.", pydep)
            return
        except ImportError:
            pass
        msg = "External dependency {dependency!r} not installed: %s" % (e,)
        raise MissingDependency(msg, pydep) from e
    if requirement.specifier and not requirement.specifier.contains(version):
        msg = f"External dependency version mismatch: {{dependency}} (installed: {version})"
        raise MissingDependency(msg, pydep)