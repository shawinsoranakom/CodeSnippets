def build(
        self,
        path: str,
        tags: list[str],
        platform: str | None = None,
        extra_build_args: list[str] | None = None,
        use_local_cache: bool = False,
    ) -> str:
        """Builds a Docker image using BuildKit and handles the build logs appropriately.

        Args:
            path (str): The path to the Docker build context.
            tags (list[str]): A list of image tags to apply to the built image.
            platform (str, optional): The target platform for the build. Defaults to None.
            use_local_cache (bool, optional): Whether to use and update the local build cache. Defaults to True.
            extra_build_args (list[str], optional): Additional arguments to pass to the Docker build command. Defaults to None.

        Returns:
            str: The name of the built Docker image.

        Raises:
            AgentRuntimeBuildError: If the Docker server version is incompatible or if the build process fails.

        Note:
            This method uses Docker BuildKit for improved build performance and caching capabilities.
            If `use_local_cache` is True, it will attempt to use and update the build cache in a local directory.
            The `extra_build_args` parameter allows for passing additional Docker build arguments as needed.
        """
        self.docker_client = docker.from_env()
        version_info = self.docker_client.version()
        server_version = version_info.get('Version', '').split('+')[0].replace('-', '.')
        components = version_info.get('Components')
        self.is_podman = (
            components is not None
            and len(components) > 0
            and components[0].get('Name', '').startswith('Podman')
        )
        if tuple(map(int, server_version.split('.'))) < (18, 9) and not self.is_podman:
            raise AgentRuntimeBuildError(
                'Docker server version must be >= 18.09 to use BuildKit'
            )

        if self.is_podman and tuple(map(int, server_version.split('.'))) < (4, 9):
            raise AgentRuntimeBuildError('Podman server version must be >= 4.9.0')

        if not DockerRuntimeBuilder.check_buildx(self.is_podman):
            # when running openhands in a container, there might not be a "docker"
            # binary available, in which case we need to download docker binary.
            # since the official openhands app image is built from debian, we use
            # debian way to install docker binary
            logger.info(
                'No docker binary available inside openhands-app container, trying to download online...'
            )
            commands = [
                'apt-get update',
                'apt-get install -y ca-certificates curl gnupg',
                'install -m 0755 -d /etc/apt/keyrings',
                'curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc',
                'chmod a+r /etc/apt/keyrings/docker.asc',
                'echo \
                  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
                  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
                  tee /etc/apt/sources.list.d/docker.list > /dev/null',
                'apt-get update',
                'apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin',
            ]
            for cmd in commands:
                try:
                    subprocess.run(
                        cmd, shell=True, check=True, stdout=subprocess.DEVNULL
                    )
                except subprocess.CalledProcessError as e:
                    logger.error(f'Image build failed:\n{e}')
                    logger.error(f'Command output:\n{e.output}')
                    raise
            logger.info('Downloaded and installed docker binary')

        target_image_hash_name = tags[0]
        target_image_repo, target_image_source_tag = target_image_hash_name.split(':')
        target_image_tag = tags[1].split(':')[1] if len(tags) > 1 else None

        buildx_cmd = [
            'docker' if not self.is_podman else 'podman',
            'buildx',
            'build',
            '--progress=plain',
            f'--build-arg=OPENHANDS_RUNTIME_VERSION={get_version()}',
            f'--build-arg=OPENHANDS_RUNTIME_BUILD_TIME={datetime.datetime.now().isoformat()}',
            f'--tag={target_image_hash_name}',
            '--load',
        ]

        # Include the platform argument only if platform is specified
        if platform:
            buildx_cmd.append(f'--platform={platform}')

        cache_dir = '/tmp/.buildx-cache'
        if use_local_cache and self._is_cache_usable(cache_dir):
            buildx_cmd.extend(
                [
                    f'--cache-from=type=local,src={cache_dir}',
                    f'--cache-to=type=local,dest={cache_dir},mode=max',
                ]
            )

        if extra_build_args:
            buildx_cmd.extend(extra_build_args)

        buildx_cmd.append(path)  # must be last!

        self.rolling_logger.start(
            f'================ {buildx_cmd[0].upper()} BUILD STARTED ================'
        )

        builder_cmd = ['docker', 'buildx', 'use', 'default']
        subprocess.Popen(
            builder_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        try:
            process = subprocess.Popen(
                buildx_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            output_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        output_lines.append(line)  # Store all output lines
                        self._output_logs(line)

            return_code = process.wait()

            if return_code != 0:
                # Use the collected output for error reporting
                output_str = '\n'.join(output_lines)
                raise subprocess.CalledProcessError(
                    return_code,
                    process.args,
                    output=output_str,  # Use the collected output
                    stderr=None,
                )

        except subprocess.CalledProcessError as e:
            logger.error(f'Image build failed with exit code {e.returncode}')
            if e.output:
                logger.error(f'Command output:\n{e.output}')
            elif self.rolling_logger.is_enabled() and self.rolling_logger.all_lines:
                logger.error(f'Docker build output:\n{self.rolling_logger.all_lines}')
            raise

        except subprocess.TimeoutExpired:
            logger.error('Image build timed out')
            raise

        except FileNotFoundError as e:
            logger.error(f'Python executable not found: {e}')
            raise

        except PermissionError as e:
            logger.error(
                f'Permission denied when trying to execute the build command:\n{e}'
            )
            raise

        except Exception as e:
            logger.error(f'An unexpected error occurred during the build process: {e}')
            raise

        logger.info(f'Image [{target_image_hash_name}] build finished.')

        if target_image_tag:
            image = self.docker_client.images.get(target_image_hash_name)
            image.tag(target_image_repo, target_image_tag)
            logger.info(
                f'Re-tagged image [{target_image_hash_name}] with more generic tag [{target_image_tag}]'
            )

        # Check if the image is built successfully
        image = self.docker_client.images.get(target_image_hash_name)
        if image is None:
            raise AgentRuntimeBuildError(
                f'Build failed: Image {target_image_hash_name} not found'
            )

        tags_str = (
            f'{target_image_source_tag}, {target_image_tag}'
            if target_image_tag
            else target_image_source_tag
        )
        logger.info(
            f'Image {target_image_repo} with tags [{tags_str}] built successfully'
        )
        return target_image_hash_name