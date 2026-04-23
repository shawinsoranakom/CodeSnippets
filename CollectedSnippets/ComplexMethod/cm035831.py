def list_files(self, path: str | None = None) -> list[str]:
        """List files in the sandbox."""
        if self.sandbox is None:
            logger.warning("Cannot list files: E2B sandbox not initialized")
            return []

        if path is None:
            path = self.config.workspace_mount_path_in_sandbox or '/workspace'

        try:
            exit_code, output = self.sandbox.execute(f"find {path} -maxdepth 1 -type f -o -type d")
            if exit_code == 0:
                files = [line.strip() for line in output.strip().split('\n') if line.strip()]
                return [f.replace(path + '/', '') if f.startswith(path + '/') else f for f in files]
            else:
                logger.warning(f"Failed to list files in {path}: {output}")
                return []
        except Exception as e:
            logger.warning(f"Error listing files: {e}")
            return []