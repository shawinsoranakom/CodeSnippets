async def test_cover(
    client: ClientSessionGenerator, cover_entities: dict[str, er.RegistryEntry]
) -> None:
    """Test prometheus metrics for cover."""
    data = {**cover_entities}
    body = await generate_latest_metrics(client)

    open_covers = ["cover_open", "cover_position", "cover_tilt_position"]
    for testcover in data:
        EntityMetric(
            metric_name="cover_state",
            domain="cover",
            friendly_name=cover_entities[testcover].original_name,
            entity=cover_entities[testcover].entity_id,
            state="open",
        ).withValue(
            1.0 if cover_entities[testcover].unique_id in open_covers else 0.0
        ).assert_in_metrics(body)

        EntityMetric(
            metric_name="cover_state",
            domain="cover",
            friendly_name=cover_entities[testcover].original_name,
            entity=cover_entities[testcover].entity_id,
            state="closed",
        ).withValue(
            1.0 if cover_entities[testcover].unique_id == "cover_closed" else 0.0
        ).assert_in_metrics(body)

        EntityMetric(
            metric_name="cover_state",
            domain="cover",
            friendly_name=cover_entities[testcover].original_name,
            entity=cover_entities[testcover].entity_id,
            state="opening",
        ).withValue(
            1.0 if cover_entities[testcover].unique_id == "cover_opening" else 0.0
        ).assert_in_metrics(body)

        EntityMetric(
            metric_name="cover_state",
            domain="cover",
            friendly_name=cover_entities[testcover].original_name,
            entity=cover_entities[testcover].entity_id,
            state="closing",
        ).withValue(
            1.0 if cover_entities[testcover].unique_id == "cover_closing" else 0.0
        ).assert_in_metrics(body)

        if testcover == "cover_position":
            EntityMetric(
                metric_name="cover_position",
                domain="cover",
                friendly_name=cover_entities[testcover].original_name,
                entity=cover_entities[testcover].entity_id,
            ).withValue(50.0).assert_in_metrics(body)

        if testcover == "cover_tilt_position":
            EntityMetric(
                metric_name="cover_tilt_position",
                domain="cover",
                friendly_name=cover_entities[testcover].original_name,
                entity=cover_entities[testcover].entity_id,
            ).withValue(50.0).assert_in_metrics(body)