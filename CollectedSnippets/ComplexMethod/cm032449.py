def _click(locator, label: str = "click") -> None:
        timeout_ms = _playwright_auth_ready_timeout_ms()
        attempts = 3
        for idx in range(attempts):
            try:
                locator.click(timeout=timeout_ms)
                return
            except PlaywrightTimeoutError as exc:
                message = str(exc).lower()
                can_force = (
                    "intercepts pointer events" in message
                    or "element was detached" in message
                    or "element is not stable" in message
                )
                if not can_force:
                    raise
                if "intercepts pointer events" in message and not _locator_is_topmost(
                    locator
                ):
                    if idx >= attempts - 1:
                        raise
                    time.sleep(0.15)
                    continue
                try:
                    if _env_bool("PW_FIXTURE_DEBUG", False):
                        print(f"[auth-click] forcing {label} attempt={idx + 1}", flush=True)
                    locator.click(force=True, timeout=timeout_ms)
                    return
                except PlaywrightTimeoutError:
                    if idx >= attempts - 1:
                        raise
                    time.sleep(0.15)