def list_containers(self, filter: list[str] | str | None = None, all=True) -> list[dict]:
        filter = [filter] if isinstance(filter, str) else filter
        cmd = self._docker_cmd()
        cmd.append("ps")
        if all:
            cmd.append("-a")
        options = []
        if filter:
            options += [y for filter_item in filter for y in ["--filter", filter_item]]
        cmd += options
        cmd.append("--format")
        cmd.append("{{json . }}")
        try:
            cmd_result = run(cmd).strip()
        except subprocess.CalledProcessError as e:
            raise ContainerException(
                f"Docker process returned with errorcode {e.returncode}", e.stdout, e.stderr
            ) from e
        container_list = []
        if cmd_result:
            if cmd_result[0] == "[":
                container_list = json.loads(cmd_result)
            else:
                container_list = [json.loads(line) for line in cmd_result.splitlines()]
        result = []
        for container in container_list:
            labels = self._transform_container_labels(container["Labels"])
            result.append(
                {
                    # support both, Docker and podman API response formats (`ID` vs `Id`)
                    "id": container.get("ID") or container["Id"],
                    "image": container["Image"],
                    # Docker returns a single string for `Names`, whereas podman returns a list of names
                    "name": ensure_list(container["Names"])[0],
                    "status": container["State"],
                    "labels": labels,
                }
            )
        return result