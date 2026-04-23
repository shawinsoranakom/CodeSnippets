async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        agent_json: dict | None = None,
        **kwargs,
    ) -> ToolResponseBase:
        session_id = session.session_id if session else None

        guide_gate = require_guide_read(session, "fix_agent_graph")
        if guide_gate is not None:
            return guide_gate

        if not agent_json or not isinstance(agent_json, dict):
            return ErrorResponse(
                message="Please provide a valid agent JSON object.",
                error="Missing or invalid agent_json parameter",
                session_id=session_id,
            )

        nodes = agent_json.get("nodes", [])

        if not nodes:
            return ErrorResponse(
                message="The agent JSON has no nodes. An agent needs at least one block.",
                error="empty_agent",
                session_id=session_id,
            )

        try:
            blocks = get_blocks_as_dicts()
            fixer = AgentFixer()
            fixed_agent = fixer.apply_all_fixes(agent_json, blocks)
            fixes_applied = fixer.get_fixes_applied()
        except Exception as e:
            logger.error(f"Fixer error: {e}", exc_info=True)
            return ErrorResponse(
                message=f"Auto-fix encountered an error: {str(e)}",
                error="fix_exception",
                session_id=session_id,
            )

        # Re-validate after fixing
        try:
            validator = AgentValidator()
            is_valid, _ = validator.validate(fixed_agent, blocks)
            remaining_errors = validator.errors if not is_valid else []
        except Exception as e:
            logger.warning(f"Post-fix validation error: {e}", exc_info=True)
            remaining_errors = [f"Post-fix validation failed: {str(e)}"]
            is_valid = False

        if is_valid:
            return FixResultResponse(
                message=(
                    f"Applied {len(fixes_applied)} fix(es). Agent graph is now valid!"
                ),
                fixed_agent_json=fixed_agent,
                fixes_applied=fixes_applied,
                fix_count=len(fixes_applied),
                valid_after_fix=True,
                remaining_errors=[],
                session_id=session_id,
            )

        return FixResultResponse(
            message=(
                f"Applied {len(fixes_applied)} fix(es), but "
                f"{len(remaining_errors)} issue(s) remain. "
                "Review the remaining errors and fix manually."
            ),
            fixed_agent_json=fixed_agent,
            fixes_applied=fixes_applied,
            fix_count=len(fixes_applied),
            valid_after_fix=False,
            remaining_errors=remaining_errors,
            session_id=session_id,
        )