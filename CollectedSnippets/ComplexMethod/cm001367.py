def test_agent_approval_auto_approves_subsequent_calls(
        self, workspace: Path, agent_dir: Path
    ):
        """After AGENT approval, subsequent calls should auto-approve.

        This tests the scenario where multiple tools are executed in sequence -
        after approving the first one with 'Always (this agent)', subsequent
        calls should be auto-approved without prompting.
        """
        workspace.mkdir(parents=True, exist_ok=True)
        prompt_count = [0]

        def mock_prompt(
            _cmd: str, _args_str: str, _args: dict
        ) -> tuple[ApprovalScope, str | None]:
            prompt_count[0] += 1
            return (ApprovalScope.AGENT, None)

        agent_permissions = AgentPermissions()
        settings = WorkspaceSettings(permissions=PermissionsConfig(allow=[], deny=[]))
        auto_approved = []

        def on_auto_approve(
            cmd: str, args_str: str, args: dict, scope: ApprovalScope
        ) -> None:
            auto_approved.append((cmd, args_str, scope))

        manager = CommandPermissionManager(
            workspace=workspace,
            agent_dir=agent_dir,
            workspace_settings=settings,
            agent_permissions=agent_permissions,
            prompt_fn=mock_prompt,
            on_auto_approve=on_auto_approve,
        )

        # First call - should prompt and approve
        result1 = manager.check_command("ask_user", {"question": "What is your name?"})
        assert result1.allowed
        assert prompt_count[0] == 1
        assert "ask_user(**)" in agent_permissions.permissions.allow

        # Second call with different args - should auto-approve without prompting
        result2 = manager.check_command("ask_user", {"question": "What is your age?"})
        assert result2.allowed
        assert prompt_count[0] == 1  # Still 1 - no new prompt!
        assert len(auto_approved) == 1
        assert auto_approved[0][0] == "ask_user"
        assert auto_approved[0][2] == ApprovalScope.AGENT

        # Third call - also auto-approved
        result3 = manager.check_command(
            "ask_user", {"question": "Do you want /path/to/file?"}
        )
        assert result3.allowed
        assert prompt_count[0] == 1  # Still 1
        assert len(auto_approved) == 2