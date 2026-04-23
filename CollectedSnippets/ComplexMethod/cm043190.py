async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if URL can be fetched according to robots.txt rules.

        Args:
            url: The URL to check
            user_agent: User agent string to check against (default: "*")

        Returns:
            bool: True if allowed, False if disallowed by robots.txt
        """
        # Handle empty/invalid URLs
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if not domain:
                return True
        except Exception as _ex:
            return True

        # Fast path - check cache first
        rules, is_fresh = self._get_cached_rules(domain)

        # If rules not found or stale, fetch new ones
        if not is_fresh:
            try:
                # Ensure we use the same scheme as the input URL
                scheme = parsed.scheme or 'http'
                robots_url = f"{scheme}://{domain}/robots.txt"

                async with aiohttp.ClientSession() as session:
                    async with session.get(robots_url, timeout=2, ssl=False) as response:
                        if response.status == 200:
                            rules = await response.text()
                            self._cache_rules(domain, rules)
                        else:
                            return True
            except Exception as _ex:
                # On any error (timeout, connection failed, etc), allow access
                return True

        if not rules:
            return True

        # Create parser for this check
        parser = RobotFileParser() 
        parser.parse(rules.splitlines())

        # If parser can't read rules, allow access
        if not parser.mtime():
            return True

        return parser.can_fetch(user_agent, url)