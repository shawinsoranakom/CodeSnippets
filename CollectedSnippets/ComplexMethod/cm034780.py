async def get_quota(cls, api_key: Optional[str] = None) -> Optional[dict]:
        session_cookie = get_cookies("ollama.com", cache_result=False).get("__Secure-session")
        if not session_cookie:
            return await super().get_quota(api_key=api_key)
        quota = {}
        try:
            async with StreamSession() as session:
                async with session.get(
                    "https://ollama.com/settings",
                    cookies={"__Secure-session": session_cookie},
                    headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                ) as response:
                    await raise_for_status(response)
                    html = await response.text()
                    lower = html.lower()
                    has_sign_in = "sign in to ollama" in lower or "log in to ollama" in lower
                    has_auth_endpoint = "/api/auth/signin" in lower or "/auth/signin" in lower or 'href="/signin"' in lower or 'href="/login"' in lower
                    has_form = "<form" in lower
                    has_password = 'type="password"' in lower or 'name="password"' in lower
                    has_email = 'type="email"' in lower or 'name="email"' in lower
                    if (has_sign_in and has_form and (has_email or has_password or has_auth_endpoint)) \
                            or (has_form and has_auth_endpoint) \
                            or (has_form and has_password and has_email):
                        raise MissingAuthError("Ollama session cookie is invalid or expired.")
                    for label in ("Session usage", "Hourly usage", "Weekly usage"):
                        idx = html.find(label)
                        if idx == -1:
                            continue
                        section = html[idx + len(label):idx + len(label) + 800]
                        pct_match = re.search(r'(\d+(?:\.\d+)?)%\s*used', section)
                        if not pct_match:
                            width_match = re.search(r'width:\s*(\d+(?:\.\d+)?)%', section)
                            if width_match:
                                pct_match = width_match
                        pct = float(pct_match.group(1)) if pct_match else None
                        reset_match = re.search(r'data-time=["\']([^"\']+)["\']', section)
                        reset_time = reset_match.group(1) if reset_match else None
                        key = label.lower().replace(" ", "_")
                        quota[key] = {
                            "used_percent": pct,
                            "reset_time": reset_time,
                        }
                    match = re.search(r'<span class="text-sm">Premium requests</span>\s*<span class="text-sm">(\d+)/(\d+) used</span>\s*</div>', html)
                    if match:
                        used = int(match.group(1))
                        total = int(match.group(2))
                        pct = (used / total) * 100 if total > 0 else None
                        quota["premium_requests"] = {
                            "used": used,
                            "total": total,
                            "used_percent": pct,
                        }
        except Exception as e:
            raise RuntimeError(f"Failed to get quota information from Ollama: {e}")
        if not quota:
            raise RuntimeError("Failed to find quota information in Ollama settings page.")
        return quota