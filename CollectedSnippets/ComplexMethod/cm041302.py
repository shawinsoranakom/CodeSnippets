def remove_container(
        self, container_name: str, force=True, check_existence=False, volumes=False
    ) -> None:
        if check_existence and container_name not in self.get_all_container_names():
            return
        cmd = self._docker_cmd() + ["rm"]
        if force:
            cmd.append("-f")
        if volumes:
            cmd.append("--volumes")
        cmd.append(container_name)
        LOG.debug("Removing container with cmd %s", cmd)
        try:
            output = run(cmd)
            # When the container does not exist, the output could have the error message without any exception
            if isinstance(output, str) and not force:
                self._check_output_and_raise_no_such_container_error(container_name, output=output)
        except subprocess.CalledProcessError as e:
            if not force:
                self._check_and_raise_no_such_container_error(container_name, error=e)
            raise ContainerException(
                f"Docker process returned with errorcode {e.returncode}", e.stdout, e.stderr
            ) from e