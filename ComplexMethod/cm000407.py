async def moderate_graph_execution_outputs(
        self,
        db_client: "DatabaseManagerAsyncClient",
        graph_exec_id: str,
        user_id: str,
        graph_id: str,
        timeout: int = 10,
    ) -> Exception | None:
        """
        Complete output moderation flow for graph execution
        Returns: error_if_failed (None means success)
        """
        if not self.config.enabled:
            return None

        # Check if AutoMod feature is enabled for this user
        if not await is_feature_enabled(Flag.AUTOMOD, user_id):
            logger.debug(f"AutoMod feature not enabled for user {user_id}")
            return None

        # Get completed executions and collect outputs
        completed_executions = await db_client.get_node_executions(
            graph_exec_id, statuses=[ExecutionStatus.COMPLETED], include_exec_data=True
        )

        if not completed_executions:
            return None

        all_outputs = []
        for exec_entry in completed_executions:
            if exec_entry.output_data:
                all_outputs.extend(str(v) for v in exec_entry.output_data.values() if v)

        if not all_outputs:
            return None

        # Combine all content and moderate directly
        content = " ".join(all_outputs)

        # Run moderation
        logger.warning(f"Moderating outputs for graph execution {graph_exec_id}")
        try:
            moderation_passed, content_id = await self._moderate_content(
                content,
                {
                    "user_id": user_id,
                    "graph_id": graph_id,
                    "graph_exec_id": graph_exec_id,
                    "moderation_type": "execution_output",
                },
            )

            if not moderation_passed:
                logger.warning(f"Moderation failed for graph execution {graph_exec_id}")
                # Update node statuses for frontend display before raising error
                await self._update_failed_nodes_for_moderation(
                    db_client, graph_exec_id, "output", content_id
                )

                return ModerationError(
                    message="Execution failed due to output content moderation",
                    user_id=user_id,
                    graph_exec_id=graph_exec_id,
                    moderation_type="output",
                    content_id=content_id,
                )

            return None

        except asyncio.TimeoutError:
            logger.warning(
                f"Output moderation timed out for graph execution {graph_exec_id}, bypassing moderation"
            )
            return None  # Bypass moderation on timeout
        except Exception as e:
            logger.warning(f"Output moderation execution failed: {e}")
            return ModerationError(
                message="Execution failed due to output content moderation error",
                user_id=user_id,
                graph_exec_id=graph_exec_id,
                moderation_type="output",
            )