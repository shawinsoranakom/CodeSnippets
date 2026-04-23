async def onboard_managed_project(self, access_token: str, tier_id: str, project_id: Optional[str] = "default-project", attempts: int = 10, delay_ms: int = 5000) -> Optional[str]:
        """
        Onboard a managed project for the user, optionally retrying until completion.

        Args:
            access_token (str): Bearer token for authorization.
            tier_id (str): Tier ID to use for onboarding.
            project_id (Optional[str]): Optional project ID to onboard.
            attempts (int): Number of retry attempts.
            delay_ms (int): Delay between retries in milliseconds.

        Returns:
            Optional[str]: Managed project ID if successful, None otherwise.
        """
        metadata = {
            "ideType": "ANTIGRAVITY",
            "pluginType": "GEMINI",
        }
        if project_id:
            metadata["duetProject"] = project_id

        request_body = {
            "tierId": tier_id,
            "metadata": metadata,
        }

        for attempt in range(attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}:onboardUser",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {access_token}",
                            "User-Agent": "GeminiCLI/1.0.0",
                        },
                        json=request_body,
                    ) as response:
                        if response.ok:
                            payload = await response.json()
                            debug.log(f"Onboarding attempt {attempt + 1}: {payload}")
                            managed_project_id = payload.get("response", {}).get("cloudaicompanionProject", {}).get("id")
                            if payload.get("done") and managed_project_id:
                                return managed_project_id
                            if payload.get("done") and project_id:
                                return project_id
                        else:
                            text = await response.text()
                            debug.error(f"Onboarding attempt {attempt + 1} failed with status {response.status}: {text}")
                        response.raise_for_status()
            except Exception as e:
                debug.error(f"Failed to onboard managed project: {e}")

            await asyncio.sleep(delay_ms / 1000)

        return None