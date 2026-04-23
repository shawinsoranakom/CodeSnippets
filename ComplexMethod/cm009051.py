def _build_command(
        self,
        workspace: Path,
        env: Mapping[str, str],
        command: Sequence[str],
    ) -> list[str]:
        binary = self._resolve_binary()
        full_command: list[str] = [binary, "run", "-i"]
        if self.remove_container_on_exit:
            full_command.append("--rm")
        if not self.network_enabled:
            full_command.extend(["--network", "none"])
        if self.memory_bytes is not None:
            full_command.extend(["--memory", str(self.memory_bytes)])
        if self._should_mount_workspace(workspace):
            host_path = str(workspace)
            full_command.extend(["-v", f"{host_path}:{host_path}"])
            full_command.extend(["-w", host_path])
        else:
            full_command.extend(["-w", "/"])
        if self.read_only_rootfs:
            full_command.append("--read-only")
        for key, value in env.items():
            full_command.extend(["-e", f"{key}={value}"])
        if self.cpus is not None:
            full_command.extend(["--cpus", self.cpus])
        if self.user is not None:
            full_command.extend(["--user", self.user])
        if self.extra_run_args:
            full_command.extend(self.extra_run_args)
        full_command.append(self.image)
        full_command.extend(command)
        return full_command