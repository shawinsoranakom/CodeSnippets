async def update_agent(tenant_id: str, agent_id: str):
    req: dict[str, Any] = {k: v for k, v in cast(dict[str, Any], (await get_request_json())).items() if v is not None}
    req["user_id"] = tenant_id

    if req.get("dsl") is not None:
        try:
            req["dsl"] = CanvasReplicaService.normalize_dsl(req["dsl"])
        except ValueError as e:
            return get_json_result(data=False, message=str(e), code=RetCode.ARGUMENT_ERROR)

    if req.get("title") is not None:
        req["title"] = req["title"].strip()

    if not UserCanvasService.query(user_id=tenant_id, id=agent_id):
        return get_json_result(
            data=False, message="Only owner of canvas authorized for this operation.",
            code=RetCode.OPERATING_ERROR)

    _, current_agent = UserCanvasService.get_by_id(agent_id)
    agent_title_for_version = req.get("title") or (current_agent.title if current_agent else "")
    owner_nickname = _get_user_nickname(tenant_id)

    UserCanvasService.update_by_id(agent_id, req)

    if req.get("dsl") is not None:
        UserCanvasVersionService.save_or_replace_latest(
            user_canvas_id=agent_id,
            title=UserCanvasVersionService.build_version_title(owner_nickname, agent_title_for_version),
            dsl=req["dsl"]
        )

    return get_json_result(data=True)