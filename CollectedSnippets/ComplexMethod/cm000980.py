async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        *,
        uuids: list[str] | None = None,
        hard_delete: bool = False,
        **kwargs,
    ) -> ToolResponseBase:
        if not user_id:
            return ErrorResponse(
                message="Authentication required.",
                session_id=session.session_id,
            )

        if not await is_enabled_for_user(user_id):
            return ErrorResponse(
                message="Memory features are not enabled for your account.",
                session_id=session.session_id,
            )

        if not uuids:
            return ErrorResponse(
                message="At least one UUID is required. Use memory_forget_search first.",
                session_id=session.session_id,
            )

        try:
            group_id = derive_group_id(user_id)
        except ValueError:
            return ErrorResponse(
                message="Invalid user ID for memory operations.",
                session_id=session.session_id,
            )

        try:
            client = await get_graphiti_client(group_id)
        except Exception:
            logger.warning(
                "Failed to get Graphiti client for user %s", user_id[:12], exc_info=True
            )
            return ErrorResponse(
                message="Memory service is temporarily unavailable.",
                session_id=session.session_id,
            )

        driver = getattr(client, "graph_driver", None) or getattr(
            client, "driver", None
        )
        if not driver:
            return ErrorResponse(
                message="Could not access graph driver for deletion.",
                session_id=session.session_id,
            )

        if hard_delete:
            deleted, failed = await _hard_delete_edges(driver, uuids, user_id)
            mode = "permanently deleted"
        else:
            deleted, failed = await _soft_delete_edges(driver, uuids, user_id)
            mode = "invalidated"

        return MemoryForgetConfirmResponse(
            message=(
                f"{len(deleted)} memory edge(s) {mode}."
                + (f" {len(failed)} failed." if failed else "")
            ),
            session_id=session.session_id,
            deleted_uuids=deleted,
            failed_uuids=failed,
        )