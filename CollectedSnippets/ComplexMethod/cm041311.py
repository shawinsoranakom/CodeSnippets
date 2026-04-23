def get_docker_image_names(
        self,
        strip_latest: bool = True,
        include_tags: bool = True,
        strip_wellknown_repo_prefixes: bool = True,
    ):
        try:
            images = self.client().images.list()
            image_names = [tag for image in images for tag in image.tags if image.tags]
            if not include_tags:
                image_names = [image_name.rpartition(":")[0] for image_name in image_names]
            if strip_wellknown_repo_prefixes:
                image_names = Util.strip_wellknown_repo_prefixes(image_names)
            if strip_latest:
                Util.append_without_latest(image_names)
            return image_names
        except APIError as e:
            raise ContainerException() from e