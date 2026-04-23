async def _refresh_server(self, server: WorkerState) -> None:
        if server.local_server is not None:
            if not server.local_server.is_running():
                try:
                    await server.local_server.restart(self.client)
                    server.base_url = normalize_base_url(server.local_server.base_url or "")
                except Exception as exc:
                    server.healthy = False
                    server.last_error = str(exc)
                    server.last_checked_at = utc_now_iso()
                    server.consecutive_health_failures += 1
                    return
            elif server.local_server.base_url is not None:
                server.base_url = normalize_base_url(server.local_server.base_url)

        if not server.base_url:
            server.healthy = False
            server.last_error = "Upstream base_url is not configured"
            server.last_checked_at = utc_now_iso()
            server.consecutive_health_failures += 1
            return

        try:
            response = await self.client.get(f"{server.base_url}{HEALTH_ENDPOINT}")
        except httpx.HTTPError as exc:
            server.healthy = False
            server.last_error = str(exc)
            server.last_checked_at = utc_now_iso()
            server.consecutive_health_failures += 1
            if (
                server.local_server is not None
                and server.consecutive_health_failures
                >= WORKER_HEALTH_FAILURE_RESTART_THRESHOLD
            ):
                await self._restart_local_server(server)
            return

        server.last_checked_at = utc_now_iso()
        if response.status_code != 200:
            server.healthy = False
            server.last_error = response_detail(response)
            server.consecutive_health_failures += 1
            if (
                server.local_server is not None
                and server.consecutive_health_failures
                >= WORKER_HEALTH_FAILURE_RESTART_THRESHOLD
            ):
                await self._restart_local_server(server)
            return

        try:
            payload = _parse_json_object_response(response, "health payload")
            self._update_server_from_health_payload(server, payload)
        except (TypeError, ValueError) as exc:
            server.healthy = False
            server.last_error = f"Invalid health payload: {exc}"
            server.consecutive_health_failures += 1
            if (
                server.local_server is not None
                and server.consecutive_health_failures
                >= WORKER_HEALTH_FAILURE_RESTART_THRESHOLD
            ):
                await self._restart_local_server(server)
            return