def __init__(self, path):
        # If we have a valid repo, git_version will be a tuple of 3+ ints:
        # (major, minor, patch, possible_additional_patch_number)
        self.git_version = None  # type: Optional[Tuple[int, ...]]

        try:
            import git

            # GitPython is not fully typed, and mypy is outputting inconsistent
            # type errors on Mac and Linux. We bypass type checking entirely
            # by re-declaring the `git` import as an "Any".
            git_package: Any = git
            self.repo = git_package.Repo(path, search_parent_directories=True)
            self.git_version = self.repo.git.version_info

            if self.git_version >= MIN_GIT_VERSION:
                git_root = self.repo.git.rev_parse("--show-toplevel")
                self.module = os.path.relpath(path, git_root)
        except Exception:
            # The git repo must be invalid for the following reasons:
            #  * git binary or GitPython not installed
            #  * No .git folder
            #  * Corrupted .git folder
            #  * Path is invalid
            self.repo = None