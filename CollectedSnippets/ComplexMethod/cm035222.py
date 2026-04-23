async def _container_to_checked_sandbox_info(self, container) -> SandboxInfo | None:
        sandbox_info = await self._container_to_sandbox_info(container)
        if (
            sandbox_info
            and self.health_check_path is not None
            and sandbox_info.exposed_urls
        ):
            app_server_url = next(
                exposed_url.url
                for exposed_url in sandbox_info.exposed_urls
                if exposed_url.name == AGENT_SERVER
            )
            try:
                # When running in Docker, replace localhost hostname with host.docker.internal for internal requests
                app_server_url = replace_localhost_hostname_for_docker(app_server_url)

                response = await self.httpx_client.get(
                    f'{app_server_url}{self.health_check_path}'
                )
                response.raise_for_status()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                # Get the started_at from the docker container info and fallback to sandbox created_at
                try:
                    state = container.attrs['State']
                    started_at = datetime.fromisoformat(state['StartedAt'])
                except Exception:
                    _logger.debug('Error getting container start time')
                    started_at = sandbox_info.created_at

                # If the server has exceeded the startup grace period, it's an error
                if started_at < utc_now() - timedelta(
                    seconds=self.startup_grace_seconds
                ):
                    _logger.info(
                        f'Sandbox server not running: {app_server_url} : {exc}'
                    )
                    sandbox_info.status = SandboxStatus.ERROR
                else:
                    _logger.debug(
                        f'Sandbox server not yet available (still starting): '
                        f'{app_server_url} : {exc}'
                    )
                    sandbox_info.status = SandboxStatus.STARTING
                sandbox_info.exposed_urls = None
                sandbox_info.session_api_key = None
        return sandbox_info