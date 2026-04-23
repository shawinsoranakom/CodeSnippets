def pull_image(
        self,
        docker_image: str,
        platform: DockerPlatform | None = None,
        log_handler: Callable[[str], None] | None = None,
        auth_config: dict[str, str] | None = None,
    ) -> None:
        self._login_if_needed(auth_config, docker_image)
        cmd = self._docker_cmd()
        docker_image = self.registry_resolver_strategy.resolve(docker_image)
        cmd += ["pull", docker_image]
        if platform:
            cmd += ["--platform", platform]
        LOG.debug("Pulling image with cmd: %s", cmd)
        try:
            result = run(cmd)
            # note: we could stream the results, but we'll just process everything at the end for now
            if log_handler:
                for line in result.split("\n"):
                    log_handler(to_str(line))
        except subprocess.CalledProcessError as e:
            stdout_str = to_str(e.stdout)
            if "pull access denied" in stdout_str:
                raise NoSuchImage(docker_image, stdout=e.stdout, stderr=e.stderr)
            # note: error message 'access to the resource is denied' raised by Podman client
            if "Trying to pull" in stdout_str and "access to the resource is denied" in stdout_str:
                raise NoSuchImage(docker_image, stdout=e.stdout, stderr=e.stderr)
            raise ContainerException(
                f"Docker process returned with errorcode {e.returncode}", e.stdout, e.stderr
            ) from e