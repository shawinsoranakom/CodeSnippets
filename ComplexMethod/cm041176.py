def __call__(self, cfg: ContainerConfiguration):
        # locate all relevant dependency directories
        pattern = self.dependency_glob
        files = _list_files_in_container_image(DOCKER_CLIENT, cfg.image_name)
        paths = [PurePosixPath(f) for f in files]
        # builds an index of "jinja2: /opt/code/.../site-packages/jinja2"
        container_path_index = {p.name: p for p in paths if p.match(pattern)}

        # find dependencies from the host
        for dep_path in self.host_paths.venv_dir.glob("lib/python3.*/site-packages/*"):
            # filter out everything that heuristically cannot be a source path
            if not self._can_be_source_path(dep_path):
                continue
            if dep_path.name.endswith(".dist-info"):
                continue
            if dep_path.name == "__pycache__":
                continue

            if dep_path.name in self.skipped_dependencies:
                continue

            if dep_path.name in container_path_index:
                # find the target path in the index if it exists
                target_path = str(container_path_index[dep_path.name])
            else:
                # if the given dependency is not in the container, then we mount it anyway
                # FIXME: we should also mount the dist-info directory. perhaps this method should be
                #  re-written completely
                target_path = self.container_paths.dependency_source(dep_path.name)

            if self._has_mount(cfg.volumes, target_path):
                continue

            cfg.volumes.append(BindMount(str(dep_path), target_path))