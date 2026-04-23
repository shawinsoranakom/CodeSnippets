def _get_tool_dir(self) -> str | None:
        """Find the tool's local directory — clone target, pip location, or binary path."""
        # 1. Check git clone target dir
        for ic in (self.INSTALL_COMMANDS or []):
            if "git clone" in ic:
                parts = ic.split()
                # If last arg is not a URL, it's a custom dir name
                repo_urls = [p for p in parts if p.startswith("http")]
                if repo_urls:
                    dirname = repo_urls[0].rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
                    # Check custom target dir (arg after URL)
                    url_idx = parts.index(repo_urls[0])
                    if url_idx + 1 < len(parts):
                        dirname = parts[url_idx + 1]
                    if os.path.isdir(dirname):
                        return os.path.abspath(dirname)

        # 2. Check binary location via which
        if self.RUN_COMMANDS:
            cmd = self.RUN_COMMANDS[0]
            if "&&" in cmd:
                # "cd foo && bar" → check "foo"
                cd_part = cmd.split("&&")[0].strip()
                if cd_part.startswith("cd "):
                    d = cd_part[3:].strip()
                    if os.path.isdir(d):
                        return os.path.abspath(d)
            binary = cmd.split()[0] if cmd else ""
            if binary.startswith("sudo"):
                binary = cmd.split()[1] if len(cmd.split()) > 1 else ""
            path = shutil.which(binary) if binary else None
            if path:
                return os.path.dirname(os.path.realpath(path))

        return None