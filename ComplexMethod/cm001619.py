def get_extensions(*, enabled, fallback_disabled_extensions=None):
    try:
        from modules import extensions
        if extensions.extensions:
            def to_json(x: extensions.Extension):
                return {
                    "name": x.name,
                    "path": x.path,
                    "commit": x.commit_hash,
                    "branch": x.branch,
                    "remote": x.remote,
                }
            return [to_json(x) for x in extensions.extensions if not x.is_builtin and x.enabled == enabled]
        else:
            return [get_info_from_repo_path(d) for d in Path(paths_internal.extensions_dir).iterdir() if d.is_dir() and enabled != (str(d.name) in fallback_disabled_extensions)]
    except Exception as e:
        return str(e)