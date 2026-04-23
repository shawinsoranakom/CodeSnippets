async def load_flow(
    user_id: str, flow_id: str | None = None, flow_name: str | None = None, tweaks: dict | None = None
) -> Graph:
    from lfx.graph.graph.base import Graph

    from langflow.processing.process import process_tweaks

    if not flow_id and not flow_name:
        msg = "Flow ID or Flow Name is required"
        raise ValueError(msg)
    if not flow_id and flow_name:
        flow_id = await find_flow(flow_name, user_id)
        if not flow_id:
            msg = f"Flow {flow_name} not found"
            raise ValueError(msg)

    async with session_scope() as session:
        graph_data = flow.data if (flow := await session.get(Flow, flow_id)) else None
    if not graph_data:
        msg = f"Flow {flow_id} not found"
        raise ValueError(msg)
    if tweaks:
        graph_data = process_tweaks(graph_data=graph_data, tweaks=tweaks)
    return Graph.from_payload(graph_data, flow_id=flow_id, user_id=user_id)