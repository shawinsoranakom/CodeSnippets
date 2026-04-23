def _process_volumes(self) -> dict[str, dict[str, str]]:
        """Process volume mounts based on configuration.

        Returns:
            A dictionary mapping host paths to container bind mounts with their modes.
        """
        # Initialize volumes dictionary
        volumes: dict[str, dict[str, str]] = {}

        # Process volumes (comma-delimited)
        if self.config.sandbox.volumes is not None:
            # Handle multiple mounts with comma delimiter
            mounts = self.config.sandbox.volumes.split(',')

            for mount in mounts:
                parts = mount.split(':')
                if len(parts) >= 2:
                    # Support both bind mounts (absolute paths) and Docker named volumes.
                    # Named volume syntax:
                    #   volume:<name>   (explicit)
                    #   <name>          (implicit when not starting with '/')
                    raw_host_part = parts[0]

                    if raw_host_part.startswith('volume:'):
                        host_path = raw_host_part.split('volume:', 1)[1]
                    elif not os.path.isabs(raw_host_part):
                        host_path = raw_host_part  # treat as named volume
                    else:
                        host_path = os.path.abspath(raw_host_part)
                    container_path = parts[1]
                    # Default mode is 'rw' if not specified
                    mount_mode = parts[2] if len(parts) > 2 else 'rw'
                    # Skip overlay mounts here; they will be handled separately via Mount objects
                    if 'overlay' in mount_mode:
                        continue

                    volumes[host_path] = {
                        'bind': container_path,
                        'mode': mount_mode,
                    }
                    logger.debug(
                        f'Mount dir (sandbox.volumes): {host_path} to {container_path} with mode: {mount_mode}'
                    )

        # Legacy mounting with workspace_* parameters
        elif (
            self.config.workspace_mount_path is not None
            and self.config.workspace_mount_path_in_sandbox is not None
        ):
            mount_mode = 'rw'  # Default mode

            # e.g. result would be: {"/home/user/openhands/workspace": {'bind': "/workspace", 'mode': 'rw'}}
            # Add os.path.abspath() here so that relative paths can be used when workspace_mount_path is configured in config.toml
            volumes[os.path.abspath(self.config.workspace_mount_path)] = {
                'bind': self.config.workspace_mount_path_in_sandbox,
                'mode': mount_mode,
            }
            logger.debug(
                f'Mount dir (legacy): {self.config.workspace_mount_path} with mode: {mount_mode}'
            )

        return volumes