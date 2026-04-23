def _find_yaml(dir):
        """Finds and returns the path to a single '.yaml' file in the specified directory, preferring files that match
        the directory name.
        """
        files = list(dir.glob("*.yaml")) or list(dir.rglob("*.yaml"))  # try root level first and then recursive
        assert files, f"No *.yaml file found in {dir}"
        if len(files) > 1:
            files = [f for f in files if f.stem == dir.stem]  # prefer *.yaml files that match dir name
            assert files, f"Multiple *.yaml files found in {dir}, only 1 *.yaml file allowed"
        assert len(files) == 1, f"Multiple *.yaml files found: {files}, only 1 *.yaml file allowed in {dir}"
        return files[0]