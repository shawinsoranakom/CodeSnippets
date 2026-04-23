def build_image(
        self,
        dockerfile_path: str,
        image_name: str,
        context_path: str = None,
        platform: DockerPlatform | None = None,
    ):
        try:
            dockerfile_path = Util.resolve_dockerfile_path(dockerfile_path)
            context_path = context_path or os.path.dirname(dockerfile_path)
            LOG.debug("Building Docker image %s from %s", image_name, dockerfile_path)
            _, logs_iterator = self.client().images.build(
                path=context_path,
                dockerfile=dockerfile_path,
                tag=image_name,
                rm=True,
                platform=platform,
            )
            # logs_iterator is a stream of dicts. Example content:
            # {'stream': 'Step 1/4 : FROM alpine'}
            # ... other build steps
            # {'aux': {'ID': 'sha256:4dcf90e87fb963e898f9c7a0451a40e36f8e7137454c65ae4561277081747825'}}
            # {'stream': 'Successfully tagged img-5201f3e1:latest\n'}
            output = ""
            for log in logs_iterator:
                if isinstance(log, dict) and ("stream" in log or "error" in log):
                    output += log.get("stream") or log["error"]
            return output
        except APIError as e:
            raise ContainerException("Unable to build Docker image") from e