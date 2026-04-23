def _process_overlay_mounts(self) -> list[Mount]:
        """Process overlay mounts specified in sandbox.volumes with mode containing 'overlay'.

        Returns:
            List of docker.types.Mount objects configured with overlay driver providing
            read-only lowerdir with per-container copy-on-write upper/work layers.
        """
        overlay_mounts: list[Mount] = []

        # No volumes configured
        if self.config.sandbox.volumes is None:
            return overlay_mounts

        # Base directory for overlay upper/work layers from env var
        overlay_base = os.environ.get('SANDBOX_VOLUME_OVERLAYS')
        if not overlay_base:
            # If no base path provided, skip overlay processing
            return overlay_mounts

        os.makedirs(overlay_base, exist_ok=True)

        mount_specs = self.config.sandbox.volumes.split(',')

        for idx, mount_spec in enumerate(mount_specs):
            parts = mount_spec.split(':')
            if len(parts) < 2:
                continue
            host_path = os.path.abspath(parts[0])
            container_path = parts[1]
            mount_mode = parts[2] if len(parts) > 2 else 'rw'

            # Only consider overlay mounts for host-bind paths (absolute)
            if (not os.path.isabs(parts[0])) or ('overlay' not in mount_mode):
                continue

            # Prepare upper and work directories unique to this container and mount
            overlay_dir = os.path.join(overlay_base, self.container_name, f'{idx}')
            upper_dir = os.path.join(overlay_dir, 'upper')
            work_dir = os.path.join(overlay_dir, 'work')
            os.makedirs(upper_dir, exist_ok=True)
            os.makedirs(work_dir, exist_ok=True)

            driver_cfg = DriverConfig(
                name='local',
                options={
                    'type': 'overlay',
                    'device': 'overlay',
                    'o': f'lowerdir={host_path},upperdir={upper_dir},workdir={work_dir}',
                },
            )

            mount = Mount(
                target=container_path,
                source='',  # Anonymous volume
                type='volume',
                labels={
                    'app': 'openhands',
                    'role': 'worker',
                    'container': self.container_name,
                },
                driver_config=driver_cfg,
            )

            overlay_mounts.append(mount)

        return overlay_mounts