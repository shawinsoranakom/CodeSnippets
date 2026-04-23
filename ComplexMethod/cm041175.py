def __call__(self, cfg: ContainerConfiguration):
        # special case for community code
        if not self.pro:
            host_path = self.host_paths.aws_community_package_dir
            if host_path.exists():
                cfg.volumes.append(
                    BindMount(
                        str(host_path), self.localstack_community_entry_points, read_only=True
                    )
                )

        # locate all relevant entry_point.txt files within the container
        pattern = self.entry_point_glob
        files = _list_files_in_container_image(DOCKER_CLIENT, cfg.image_name)
        paths = [PurePosixPath(f) for f in files]
        paths = [p for p in paths if p.match(pattern)]

        # then, check whether they exist in some form on the host within the workspace directory
        for container_path in paths:
            dep_path = container_path.parent.name.removesuffix(".dist-info")
            dep, ver = dep_path.split("-")

            if dep == "localstack_core":
                host_path = self.host_paths.localstack_project_dir / "plux.ini"
                if host_path.is_file():
                    cfg.volumes.add(
                        BindMount(
                            str(host_path),
                            str(container_path),
                            read_only=True,
                        )
                    )
            elif dep == "localstack_ext":
                host_path = (
                    self.host_paths.localstack_pro_project_dir / "localstack-pro-core" / "plux.ini"
                )
                if host_path.is_file():
                    cfg.volumes.add(
                        BindMount(
                            str(host_path),
                            str(container_path),
                            read_only=True,
                        )
                    )
            else:
                for host_path in self.host_paths.workspace_dir.glob(
                    f"*/{dep}.egg-info/entry_points.txt"
                ):
                    cfg.volumes.add(BindMount(str(host_path), str(container_path), read_only=True))
                    break