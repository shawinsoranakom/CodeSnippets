def _ripgrep_search(
        self, pattern: str, base_path: str, include: str | None
    ) -> dict[str, list[tuple[int, str]]]:
        """Search using ripgrep subprocess."""
        try:
            base_full = self._validate_and_resolve_path(base_path)
        except ValueError:
            return {}

        if not base_full.exists():
            return {}

        # Build ripgrep command
        cmd = ["rg", "--json"]

        if include:
            # Convert glob pattern to ripgrep glob
            cmd.extend(["--glob", include])

        cmd.extend(["--", pattern, str(base_full)])

        try:
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to Python search if ripgrep unavailable or times out
            return self._python_search(pattern, base_path, include)

        # Parse ripgrep JSON output
        results: dict[str, list[tuple[int, str]]] = {}
        for line in result.stdout.splitlines():
            try:
                data = json.loads(line)
                if data["type"] == "match":
                    path = data["data"]["path"]["text"]
                    # Convert to virtual path
                    virtual_path = "/" + str(Path(path).relative_to(self.root_path))
                    line_num = data["data"]["line_number"]
                    line_text = data["data"]["lines"]["text"].rstrip("\n")

                    if virtual_path not in results:
                        results[virtual_path] = []
                    results[virtual_path].append((line_num, line_text))
            except (json.JSONDecodeError, KeyError):
                continue

        return results