def build(
        self,
        path: str,
        tags: list[str],
        platform: str | None = None,
        extra_build_args: list[str] | None = None,
    ) -> str:
        """Builds a Docker image using the Runtime API's /build endpoint."""
        # Create a tar archive of the build context
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
            tar.add(path, arcname='.')
        tar_buffer.seek(0)

        # Encode the tar file as base64
        base64_encoded_tar = base64.b64encode(tar_buffer.getvalue()).decode('utf-8')

        # Prepare the multipart form data
        files = [
            ('context', ('context.tar.gz', base64_encoded_tar)),
            ('target_image', (None, tags[0])),
        ]

        # Add additional tags if present
        for tag in tags[1:]:
            files.append(('tags', (None, tag)))

        # Send the POST request to /build (Begins the build process)
        try:
            response = send_request(
                self.session,
                'POST',
                f'{self.api_url}/build',
                files=files,
                timeout=30,
            )
        except httpx.HTTPStatusError as e:
            if e.response and e.response.status_code == 429:
                logger.warning('Build was rate limited. Retrying in 30 seconds.')
                time.sleep(30)
                return self.build(path, tags, platform)
            else:
                raise e

        build_data = response.json()
        build_id = build_data['build_id']
        logger.info(f'Build initiated with ID: {build_id}')

        # Poll /build_status until the build is complete
        start_time = time.time()
        timeout = 30 * 60  # 20 minutes in seconds
        while should_continue():
            if time.time() - start_time > timeout:
                logger.error('Build timed out after 30 minutes')
                raise AgentRuntimeBuildError('Build timed out after 30 minutes')

            status_response = send_request(
                self.session,
                'GET',
                f'{self.api_url}/build_status',
                params={'build_id': build_id},
            )

            if status_response.status_code != 200:
                logger.error(f'Failed to get build status: {status_response.text}')
                raise AgentRuntimeBuildError(
                    f'Failed to get build status: {status_response.text}'
                )

            status_data = status_response.json()
            status = status_data['status']
            logger.info(f'Build status: {status}')

            if status == 'SUCCESS':
                logger.debug(f'Successfully built {status_data["image"]}')
                return str(status_data['image'])
            elif status in [
                'FAILURE',
                'INTERNAL_ERROR',
                'TIMEOUT',
                'CANCELLED',
                'EXPIRED',
            ]:
                error_message = status_data.get(
                    'error', f'Build failed with status: {status}. Build ID: {build_id}'
                )
                logger.error(error_message)
                raise AgentRuntimeBuildError(error_message)

            # Wait before polling again
            sleep_if_should_continue(30)

        raise AgentRuntimeBuildError('Build interrupted')