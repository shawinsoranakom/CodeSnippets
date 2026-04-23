async def _fetch_project_id(cls, session: aiohttp.ClientSession, access_token: str) -> str:
        """Fetch project ID from Antigravity API."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            **ANTIGRAVITY_AUTH_HEADERS,
        }

        load_request = {
            "metadata": {
                "ideType": "IDE_UNSPECIFIED",
                "platform": "PLATFORM_UNSPECIFIED",
                "pluginType": "GEMINI",
            }
        }

        # Try endpoints in order with short timeout
        timeout = aiohttp.ClientTimeout(total=10)
        for base_url in BASE_URLS:
            try:
                url = f"{base_url}:loadCodeAssist"
                async with session.post(url, headers=headers, json=load_request, timeout=timeout) as resp:
                    if resp.ok:
                        data = await resp.json()
                        project = data.get("cloudaicompanionProject")
                        if isinstance(project, dict):
                            project = project.get("id")
                        if project:
                            return project
            except asyncio.TimeoutError:
                debug.log(f"Project discovery timed out at {base_url}")
                continue
            except Exception as e:
                debug.log(f"Project discovery failed at {base_url}: {e}")
                continue
        # If discovery failed, attempt to onboard a managed project for the user.
        # Read optional configuration from environment
        attempts = int(os.environ.get("ANTIGRAVITY_ONBOARD_ATTEMPTS", "10"))
        delay_seconds = float(os.environ.get("ANTIGRAVITY_ONBOARD_DELAY_S", "5"))
        tier_id = os.environ.get("ANTIGRAVITY_TIER_ID", "free-tier")
        # Use any preconfigured project id as metadata if available
        configured_project = os.environ.get("ANTIGRAVITY_PROJECT_ID", "")

        if tier_id:
            onboard_request_body = {"tierId": tier_id, "metadata": {}}
            if configured_project:
                # include requested project id in metadata
                onboard_request_body["metadata"]["cloudaicompanionProject"] = configured_project

            # Try onboarding across endpoints with retries
            for base_url in BASE_URLS:
                for attempt in range(attempts):
                    try:
                        url = f"{base_url}:onboardUser"
                        onboard_headers = {
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                            **ANTIGRAVITY_HEADERS,
                        }
                        async with session.post(url, headers=onboard_headers, json=onboard_request_body, timeout=timeout) as resp:
                            if not resp.ok:
                                print(f"Onboarding attempt {attempt+1} at {base_url} failed with status {resp.status}")
                                print(await resp.text())
                                # Stop attempts on this endpoint and try next base_url
                                break

                            payload = await resp.json()
                            # payload.response?.cloudaicompanionProject?.id
                            response_obj = payload.get("response") or {}
                            managed = response_obj.get("cloudaicompanionProject")
                            if isinstance(managed, dict):
                                managed_id = managed.get("id")
                            else:
                                managed_id = None

                            done = bool(payload.get("done", False))
                            if done and managed_id:
                                return managed_id
                            if done and configured_project:
                                return configured_project
                    except Exception as e:
                        debug.log(f"Failed to onboard managed project at {base_url}: {e}")
                        break

                    await asyncio.sleep(delay_seconds)

        return ""