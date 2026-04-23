def check_command(
        self, command_name: str, arguments: dict[str, Any]
    ) -> PermissionCheckResult:
        """Check if command execution is allowed. Prompts if needed.

        Args:
            command_name: Name of the command to check.
            arguments: Command arguments.

        Returns:
            PermissionCheckResult with allowed status, scope, and optional feedback.
        """
        args_str = self._format_args(command_name, arguments)
        perm_string = f"{command_name}({args_str})"

        # 1. Check agent deny list
        if self._matches_patterns(
            command_name, args_str, self.agent_permissions.permissions.deny
        ):
            return PermissionCheckResult(False, ApprovalScope.DENY)

        # 2. Check workspace deny list
        if self._matches_patterns(
            command_name, args_str, self.workspace_settings.permissions.deny
        ):
            return PermissionCheckResult(False, ApprovalScope.DENY)

        # 3. Check agent allow list
        if self._matches_patterns(
            command_name, args_str, self.agent_permissions.permissions.allow
        ):
            if self.on_auto_approve:
                self.on_auto_approve(
                    command_name, args_str, arguments, ApprovalScope.AGENT
                )
            return PermissionCheckResult(True, ApprovalScope.AGENT)

        # 4. Check workspace allow list
        if self._matches_patterns(
            command_name, args_str, self.workspace_settings.permissions.allow
        ):
            if self.on_auto_approve:
                self.on_auto_approve(
                    command_name, args_str, arguments, ApprovalScope.WORKSPACE
                )
            return PermissionCheckResult(True, ApprovalScope.WORKSPACE)

        # 5. Check session denials
        if perm_string in self._session_denied:
            return PermissionCheckResult(False, ApprovalScope.DENY)

        # 6. Prompt user
        if self.prompt_fn is None:
            return PermissionCheckResult(False, ApprovalScope.DENY)

        scope, feedback = self.prompt_fn(command_name, args_str, arguments)
        pattern = self._generalize_pattern(command_name, args_str)

        if scope == ApprovalScope.ONCE:
            # Allow this one time only, don't save anywhere
            return PermissionCheckResult(True, ApprovalScope.ONCE, feedback)
        elif scope == ApprovalScope.WORKSPACE:
            self.workspace_settings.add_permission(pattern, self.workspace)
            return PermissionCheckResult(True, ApprovalScope.WORKSPACE, feedback)
        elif scope == ApprovalScope.AGENT:
            self.agent_permissions.add_permission(pattern, self.agent_dir)
            return PermissionCheckResult(True, ApprovalScope.AGENT, feedback)
        else:
            # Denied - feedback goes to agent instead of execution
            self._session_denied.add(perm_string)
            return PermissionCheckResult(False, ApprovalScope.DENY, feedback)