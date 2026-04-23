def from_db(  # type: ignore[reportIncompatibleMethodOverride]
        cls,
        graph: AgentGraph,
        for_export: bool = False,
        sub_graphs: list[AgentGraph] | None = None,
    ) -> Self:
        return cls(
            id=graph.id,
            user_id=graph.userId if not for_export else "",
            version=graph.version,
            forked_from_id=graph.forkedFromId,
            forked_from_version=graph.forkedFromVersion,
            created_at=graph.createdAt,
            is_active=graph.isActive,
            name=graph.name or "",
            description=graph.description or "",
            instructions=graph.instructions,
            recommended_schedule_cron=graph.recommendedScheduleCron,
            nodes=[NodeModel.from_db(node, for_export) for node in graph.Nodes or []],
            links=list(
                {
                    Link.from_db(link)
                    for node in graph.Nodes or []
                    for link in (node.Input or []) + (node.Output or [])
                }
            ),
            sub_graphs=[
                GraphModel.from_db(sub_graph, for_export)
                for sub_graph in sub_graphs or []
            ],
        )