def push_image(self, docker_image: str, auth_config: dict[str, str] | None = None) -> None:
        LOG.debug("Pushing Docker image: %s", docker_image)
        kwargs: dict[str, dict[str, str]] = {}
        if auth_config:
            kwargs["auth_config"] = auth_config
        try:
            result = self.client().images.push(docker_image, **kwargs)
            # some SDK clients (e.g., 5.0.0) seem to return an error string, instead of raising
            if isinstance(result, (str, bytes)) and '"errorDetail"' in to_str(result):
                if "image does not exist locally" in to_str(result):
                    raise NoSuchImage(docker_image)
                if "is denied" in to_str(result):
                    raise AccessDenied(docker_image)
                if "requesting higher privileges than access token allows" in to_str(result):
                    raise AccessDenied(docker_image)
                if "access token has insufficient scopes" in to_str(result):
                    raise AccessDenied(docker_image)
                if "authorization failed: no basic auth credentials" in to_str(result):
                    raise AccessDenied(docker_image)
                if "401 Unauthorized" in to_str(result):
                    raise AccessDenied(docker_image)
                if "no basic auth credentials" in to_str(result):
                    raise AccessDenied(docker_image)
                if "unauthorized: authentication required" in to_str(result):
                    raise AccessDenied(docker_image)
                if "insufficient_scope: authorization failed" in to_str(result):
                    raise AccessDenied(docker_image)
                if "connection refused" in to_str(result):
                    raise RegistryConnectionError(result)
                if "failed to do request:" in to_str(result):
                    raise RegistryConnectionError(result)
                raise ContainerException(result)
        except ImageNotFound:
            raise NoSuchImage(docker_image)
        except APIError as e:
            # note: error message 'image not known' raised by Podman API
            if "image not known" in str(e):
                raise NoSuchImage(docker_image)
            raise ContainerException() from e