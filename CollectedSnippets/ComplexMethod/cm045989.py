async def wait_until_ready(
        self,
        client: httpx.AsyncClient,
        timeout_seconds: float = LOCAL_API_STARTUP_TIMEOUT_SECONDS,
    ) -> None:
        assert self.base_url is not None
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        last_error: str | None = None
        while asyncio.get_running_loop().time() < deadline:
            if self.process is not None and self.process.poll() is not None:
                raise RuntimeError(f"Local worker {self.server_id} exited before becoming healthy")
            try:
                response = await client.get(f"{self.base_url}{HEALTH_ENDPOINT}")
                if response.status_code == 200:
                    return
                last_error = response_detail(response)
            except httpx.HTTPError as exc:
                last_error = str(exc)
            await asyncio.sleep(TASK_STATUS_POLL_INTERVAL_SECONDS)

        message = f"Timed out waiting for local worker {self.server_id} to become healthy"
        if last_error:
            message = f"{message}: {last_error}"
        raise RuntimeError(message)