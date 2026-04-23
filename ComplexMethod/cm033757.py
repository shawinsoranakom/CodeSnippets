def get_paths(self, path: str) -> list[str]:
        """Return the list of available content paths under the given path."""
        paths = self.__get_paths(path)

        try:
            submodule_paths = Git(path).get_submodule_paths()
        except SubprocessError:
            if path == self.root:
                raise

            # older versions of git require submodule commands to be executed from the top level of the working tree
            # git version 2.18.1 (centos8) does not have this restriction
            # git version 1.8.3.1 (centos7) does
            # fall back to using the top level directory of the working tree only when needed
            # this avoids penalizing newer git versions with a potentially slower analysis due to additional submodules
            rel_path = os.path.relpath(path, self.root) + os.path.sep

            submodule_paths = Git(self.root).get_submodule_paths()
            submodule_paths = [os.path.relpath(p, rel_path) for p in submodule_paths if p.startswith(rel_path)]

        for submodule_path in submodule_paths:
            submodule_full_path = os.path.join(path, submodule_path)

            if not os.path.exists(submodule_full_path):
                display.warning(f"Missing submodule: {submodule_path}")
                continue

            paths.extend(os.path.join(submodule_path, p) for p in self.__get_paths(submodule_full_path))

        # git reports submodule directories as regular files
        paths = [p for p in paths if p not in submodule_paths]

        return paths