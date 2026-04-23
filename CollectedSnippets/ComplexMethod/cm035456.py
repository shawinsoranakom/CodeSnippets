def image_exists(self, image_name: str, pull_from_repo: bool = True) -> bool:
        """Check if the image exists in the registry (try to pull it first) or in the local store.

        Args:
            image_name (str): The Docker image to check (<image repo>:<image tag>)
            pull_from_repo (bool): Whether to pull from the remote repo if the image not present locally
        Returns:
            bool: Whether the Docker image exists in the registry or in the local store
        """
        if not image_name:
            logger.error(f'Invalid image name: `{image_name}`')
            return False

        try:
            logger.debug(f'Checking, if image exists locally:\n{image_name}')
            self.docker_client.images.get(image_name)
            logger.debug('Image found locally.')
            return True
        except docker.errors.ImageNotFound:
            if not pull_from_repo:
                logger.debug(
                    f'Image {image_name} {colorize("not found", TermColor.WARNING)} locally'
                )
                return False
            try:
                logger.debug(
                    'Image not found locally. Trying to pull it, please wait...'
                )

                layers: dict[str, dict[str, str]] = {}
                previous_layer_count = 0

                if ':' in image_name:
                    image_repo, image_tag = image_name.split(':', 1)
                else:
                    image_repo = image_name
                    image_tag = None

                for line in self.docker_client.api.pull(
                    image_repo, tag=image_tag, stream=True, decode=True
                ):
                    self._output_build_progress(line, layers, previous_layer_count)
                    previous_layer_count = len(layers)
                logger.debug('Image pulled')
                return True
            except docker.errors.ImageNotFound:
                logger.debug('Could not find image locally or in registry.')
                return False
            except Exception as e:
                msg = f'Image {colorize("could not be pulled", TermColor.ERROR)}: '
                ex_msg = str(e)
                if 'Not Found' in ex_msg:
                    msg += 'image not found in registry.'
                else:
                    msg += f'{ex_msg}'
                logger.debug(msg)
                return False