async def get_recommended_agents(user_id: str) -> list[StoreAgentDetails]:
    user_onboarding = await get_user_onboarding(user_id)
    categories = REASON_MAPPING.get(user_onboarding.usageReason or "", [])

    where_clause: dict[str, Any] = {}

    custom = _clean_and_split((user_onboarding.usageReason or "").lower())

    if categories:
        where_clause["OR"] = [
            {"categories": {"has": category}} for category in categories
        ]
    else:
        where_clause["OR"] = [
            {"description": {"contains": word, "mode": "insensitive"}}
            for word in custom
        ]

    where_clause["OR"] += [
        {"description": {"contains": word, "mode": "insensitive"}}
        for word in user_onboarding.integrations
    ]

    where_clause["is_available"] = True

    # Try to take only agents that are available and allowed for onboarding
    storeAgents = await prisma.models.StoreAgent.prisma().find_many(
        where={
            "is_available": True,
            "use_for_onboarding": True,
        },
        order=[
            {"featured": "desc"},
            {"runs": "desc"},
            {"rating": "desc"},
        ],
        take=100,
    )

    # If not enough agents found, relax the use_for_onboarding filter
    if len(storeAgents) < 2:
        storeAgents = await prisma.models.StoreAgent.prisma().find_many(
            where=prisma.types.StoreAgentWhereInput(**where_clause),
            order=[
                {"featured": "desc"},
                {"runs": "desc"},
                {"rating": "desc"},
            ],
            take=100,
        )

    # Calculate points for the first X agents and choose the top 2
    agent_points: list[tuple[prisma.models.StoreAgent, int]] = []
    for agent in storeAgents[:POINTS_AGENT_COUNT]:
        points = _calculate_points(
            agent, categories, custom, user_onboarding.integrations
        )
        agent_points.append((agent, points))

    agent_points.sort(key=lambda x: x[1], reverse=True)
    recommended_agents = [agent for agent, _ in agent_points[:2]]

    return [StoreAgentDetails.from_db(agent) for agent in recommended_agents]