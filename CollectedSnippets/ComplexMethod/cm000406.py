async def moderate_graph_execution_inputs(
        self, db_client: "DatabaseManagerAsyncClient", graph_exec, timeout: int = 10
    ) -> Exception | None:
        """
        Complete input moderation flow for graph execution
        Returns: error_if_failed (None means success)
        """
        if not self.config.enabled:
            return None

        # Check if AutoMod feature is enabled for this user
        if not await is_feature_enabled(Flag.AUTOMOD, graph_exec.user_id):
            logger.debug(f"AutoMod feature not enabled for user {graph_exec.user_id}")
            return None

        # Get graph model and collect all inputs
        graph_model = await db_client.get_graph(
            graph_exec.graph_id,
            user_id=graph_exec.user_id,
            version=graph_exec.graph_version,
        )

        if not graph_model or not graph_model.nodes:
            return None

        all_inputs = []
        for node in graph_model.nodes:
            if node.input_default:
                all_inputs.extend(str(v) for v in node.input_default.values() if v)
            if (masks := graph_exec.nodes_input_masks) and (mask := masks.get(node.id)):
                all_inputs.extend(str(v) for v in mask.values() if v)

        if not all_inputs:
            return None

        # Combine all content and moderate directly
        content = " ".join(all_inputs)

        # Run moderation
        logger.warning(
            f"Moderating inputs for graph execution {graph_exec.graph_exec_id}"
        )
        try:
            moderation_passed, content_id = await self._moderate_content(
                content,
                {
                    "user_id": graph_exec.user_id,
                    "graph_id": graph_exec.graph_id,
                    "graph_exec_id": graph_exec.graph_exec_id,
                    "moderation_type": "execution_input",
                },
            )

            if not moderation_passed:
                logger.warning(
                    f"Moderation failed for graph execution {graph_exec.graph_exec_id}"
                )
                # Update node statuses for frontend display before raising error
                await self._update_failed_nodes_for_moderation(
                    db_client, graph_exec.graph_exec_id, "input", content_id
                )

                return ModerationError(
                    message="Execution failed due to input content moderation",
                    user_id=graph_exec.user_id,
                    graph_exec_id=graph_exec.graph_exec_id,
                    moderation_type="input",
                    content_id=content_id,
                )

            return None

        except asyncio.TimeoutError:
            logger.warning(
                f"Input moderation timed out for graph execution {graph_exec.graph_exec_id}, bypassing moderation"
            )
            return None  # Bypass moderation on timeout
        except Exception as e:
            logger.warning(f"Input moderation execution failed: {e}")
            return ModerationError(
                message="Execution failed due to input content moderation error",
                user_id=graph_exec.user_id,
                graph_exec_id=graph_exec.graph_exec_id,
                moderation_type="input",
            )