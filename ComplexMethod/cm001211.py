def from_db(
        agent: prisma.models.LibraryAgent,
        sub_graphs: Optional[list[prisma.models.AgentGraph]] = None,
        store_listing: Optional[prisma.models.StoreListing] = None,
        profile: Optional[prisma.models.Profile] = None,
        execution_count_override: Optional[int] = None,
        schedule_info: Optional[dict[str, str]] = None,
    ) -> "LibraryAgent":
        """
        Factory method that constructs a LibraryAgent from a Prisma LibraryAgent
        model instance.
        """
        if not agent.AgentGraph:
            raise ValueError("Associated Agent record is required.")

        graph = GraphModel.from_db(agent.AgentGraph, sub_graphs=sub_graphs)

        created_at = agent.createdAt

        agent_updated_at = agent.AgentGraph.updatedAt
        lib_agent_updated_at = agent.updatedAt

        updated_at = (
            max(agent_updated_at, lib_agent_updated_at)
            if agent_updated_at
            else lib_agent_updated_at
        )

        creator_name = "Unknown"
        creator_image_url = ""
        if agent.Creator:
            creator_name = agent.Creator.name or "Unknown"
            creator_image_url = agent.Creator.avatarUrl or ""

        week_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            days=7
        )
        executions = agent.AgentGraph.Executions or []
        status_result = _calculate_agent_status(executions, week_ago)
        status = status_result.status
        new_output = status_result.new_output

        execution_count = (
            execution_count_override
            if execution_count_override is not None
            else len(executions)
        )
        success_rate: float | None = None
        avg_correctness_score: float | None = None
        if executions and execution_count > 0:
            success_count = sum(
                1
                for e in executions
                if e.executionStatus == prisma.enums.AgentExecutionStatus.COMPLETED
            )
            success_rate = (success_count / execution_count) * 100

            correctness_scores = []
            for e in executions:
                if e.stats and isinstance(e.stats, dict):
                    score = e.stats.get("correctness_score")
                    if score is not None and isinstance(score, (int, float)):
                        correctness_scores.append(float(score))
            if correctness_scores:
                avg_correctness_score = sum(correctness_scores) / len(
                    correctness_scores
                )

        recent_executions: list[RecentExecution] = []
        for e in executions:
            exec_score: float | None = None
            exec_summary: str | None = None
            if e.stats and isinstance(e.stats, dict):
                score = e.stats.get("correctness_score")
                if score is not None and isinstance(score, (int, float)):
                    exec_score = float(score)
                summary = e.stats.get("activity_status")
                if summary is not None and isinstance(summary, str):
                    exec_summary = summary
            exec_status = (
                e.executionStatus.value
                if hasattr(e.executionStatus, "value")
                else str(e.executionStatus)
            )
            recent_executions.append(
                RecentExecution(
                    status=exec_status,
                    correctness_score=exec_score,
                    activity_summary=exec_summary,
                )
            )

        can_access_graph = agent.AgentGraph.userId == agent.userId
        is_latest_version = True

        marketplace_listing_data = None
        if store_listing and store_listing.ActiveVersion and profile:
            creator_data = MarketplaceListingCreator(
                name=profile.name,
                id=profile.id,
                slug=profile.username,
            )
            marketplace_listing_data = MarketplaceListing(
                id=store_listing.id,
                name=store_listing.ActiveVersion.name,
                slug=store_listing.slug,
                creator=creator_data,
            )

        return LibraryAgent(
            id=agent.id,
            graph_id=agent.agentGraphId,
            graph_version=agent.agentGraphVersion,
            image_url=agent.imageUrl,
            creator_name=creator_name,
            creator_image_url=creator_image_url,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            name=graph.name,
            description=graph.description,
            instructions=graph.instructions,
            input_schema=graph.input_schema,
            output_schema=graph.output_schema,
            credentials_input_schema=(
                graph.credentials_input_schema if sub_graphs is not None else None
            ),
            has_external_trigger=graph.has_external_trigger,
            has_human_in_the_loop=graph.has_human_in_the_loop,
            has_sensitive_action=graph.has_sensitive_action,
            trigger_setup_info=graph.trigger_setup_info,
            new_output=new_output,
            execution_count=execution_count,
            success_rate=success_rate,
            avg_correctness_score=avg_correctness_score,
            recent_executions=recent_executions,
            can_access_graph=can_access_graph,
            is_latest_version=is_latest_version,
            is_favorite=agent.isFavorite,
            folder_id=agent.folderId,
            folder_name=agent.Folder.name if agent.Folder else None,
            recommended_schedule_cron=agent.AgentGraph.recommendedScheduleCron,
            is_scheduled=bool(schedule_info and agent.agentGraphId in schedule_info),
            next_scheduled_run=(
                schedule_info.get(agent.agentGraphId) if schedule_info else None
            ),
            settings=_parse_settings(agent.settings),
            marketplace_listing=marketplace_listing_data,
        )