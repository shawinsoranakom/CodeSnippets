def get_individual_sponsors(
    settings: Settings,
) -> defaultdict[float, dict[str, SponsorEntity]]:
    nodes: list[SponsorshipAsMaintainerNode] = []
    edges = get_graphql_sponsor_edges(settings=settings)

    while edges:
        for edge in edges:
            nodes.append(edge.node)
        last_edge = edges[-1]
        edges = get_graphql_sponsor_edges(settings=settings, after=last_edge.cursor)

    tiers: defaultdict[float, dict[str, SponsorEntity]] = defaultdict(dict)
    for node in nodes:
        tiers[node.tier.monthlyPriceInDollars][node.sponsorEntity.login] = (
            node.sponsorEntity
        )
    return tiers