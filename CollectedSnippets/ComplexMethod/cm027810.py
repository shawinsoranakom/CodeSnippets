def evaluate(self, action: Action) -> Optional[PolicyResult]:
        # Check if action involves file paths
        path = None
        if action.kwargs.get("path"):
            path = action.kwargs["path"]
        elif action.kwargs.get("file_path"):
            path = action.kwargs["file_path"]
        elif action.args and isinstance(action.args[0], str) and "/" in action.args[0]:
            path = action.args[0]

        if not path:
            return None  # Rule doesn't apply

        path = os.path.abspath(os.path.expanduser(path))

        # Check denied paths first
        for denied in self.denied_paths:
            if path.startswith(os.path.abspath(denied)):
                return PolicyResult(
                    decision=Decision.DENY,
                    reason=f"Path '{path}' matches denied pattern '{denied}'",
                    policy_name=self.name
                )

        # Check if path is in allowed paths
        for allowed in self.allowed_paths:
            if path.startswith(os.path.abspath(allowed)):
                return PolicyResult(
                    decision=Decision.ALLOW,
                    reason=f"Path '{path}' is within allowed directory '{allowed}'",
                    policy_name=self.name
                )

        # Default deny if not explicitly allowed
        return PolicyResult(
            decision=Decision.DENY,
            reason=f"Path '{path}' is outside allowed directories",
            policy_name=self.name
        )