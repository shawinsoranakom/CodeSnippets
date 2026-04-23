def push_image(self, docker_image: str, auth_config: dict[str, str] | None = None) -> None:
        self._login_if_needed(auth_config, docker_image)
        cmd = self._docker_cmd()
        cmd += ["push", docker_image]
        LOG.debug("Pushing image with cmd: %s", cmd)
        try:
            run(cmd)
        except subprocess.CalledProcessError as e:
            if "is denied" in to_str(e.stdout):
                raise AccessDenied(docker_image)
            if "requesting higher privileges than access token allows" in to_str(e.stdout):
                raise AccessDenied(docker_image)
            if "access token has insufficient scopes" in to_str(e.stdout):
                raise AccessDenied(docker_image)
            if "authorization failed: no basic auth credentials" in to_str(e.stdout):
                raise AccessDenied(docker_image)
            if "failed to authorize: failed to fetch oauth token" in to_str(e.stdout):
                raise AccessDenied(docker_image)
            if "insufficient_scope: authorization failed" in to_str(e.stdout):
                raise AccessDenied(docker_image)
            if "does not exist" in to_str(e.stdout):
                raise NoSuchImage(docker_image)
            if "connection refused" in to_str(e.stdout):
                raise RegistryConnectionError(e.stdout)
            if "failed to do request:" in to_str(e.stdout):
                raise RegistryConnectionError(e.stdout)
            # note: error message 'image not known' raised by Podman client
            if "image not known" in to_str(e.stdout):
                raise NoSuchImage(docker_image)
            raise ContainerException(
                f"Docker process returned with errorcode {e.returncode}", e.stdout, e.stderr
            ) from e