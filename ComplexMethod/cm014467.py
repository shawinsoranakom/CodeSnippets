def matched_files_iter(
        root_path: str,
        includes: Iterable = (),
        ignores: Iterable = (),
        extensions: Iterable = (),
        out_of_place_only: bool = False,
        is_pytorch_extension: bool = False) -> Iterator[str]:

    exact_matches = set(includes)

    # This is a very rough heuristic; really, we want to avoid scanning
    # any file which is not checked into source control, but this script
    # needs to work even if you're in a Git or Hg checkout, so easier to
    # just block the biggest time sinks that won't matter in the
    # end.
    for (abs_dirpath, dirs, filenames) in os.walk(root_path, topdown=True):
        rel_dirpath = os.path.relpath(abs_dirpath, root_path)
        if rel_dirpath == '.':
            # Blah blah blah O(n) blah blah
            if ".git" in dirs:
                dirs.remove(".git")
            if "build" in dirs:
                dirs.remove("build")
            if "third_party" in dirs:
                dirs.remove("third_party")
                dirs.append("third_party/nvfuser")
        for filename in filenames:
            filepath = _to_unix_path(os.path.join(abs_dirpath, filename))
            # We respect extensions, UNLESS you wrote the entire
            # filename verbatim, in which case we always accept it
            if (
                _fnmatch(filepath, includes)
                and (not _fnmatch(filepath, ignores))
                and (match_extensions(filepath, extensions) or filepath in exact_matches)
            ):
                yield filepath