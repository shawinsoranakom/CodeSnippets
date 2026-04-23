def evaluate(self, action: Action) -> Optional[PolicyResult]:
        # Check if action involves URLs or domains
        url = None
        for key in ["url", "endpoint", "domain", "host"]:
            if key in action.kwargs:
                url = action.kwargs[key]
                break

        if not url:
            # Check args for URL patterns
            for arg in action.args:
                if isinstance(arg, str) and ("http://" in arg or "https://" in arg):
                    url = arg
                    break

        if not url:
            return None  # Rule doesn't apply

        # Extract domain from URL
        domain_match = re.search(r"https?://([^/]+)", url)
        if domain_match:
            domain = domain_match.group(1)
        else:
            domain = url

        # Check if domain is allowed
        for allowed in self.allowed_domains:
            if domain == allowed or domain.endswith("." + allowed):
                return PolicyResult(
                    decision=Decision.ALLOW,
                    reason=f"Domain '{domain}' is in allowlist",
                    policy_name=self.name
                )

        if self.block_all_others:
            return PolicyResult(
                decision=Decision.DENY,
                reason=f"Domain '{domain}' not in allowlist",
                policy_name=self.name
            )

        return None