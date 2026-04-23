def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Travis CI sensor."""

    token = config[CONF_API_KEY]
    repositories = config[CONF_REPOSITORY]
    branch = config[CONF_BRANCH]

    try:
        travis = TravisPy.github_auth(token)
        user = travis.user()

    except TravisError as ex:
        _LOGGER.error("Unable to connect to Travis CI service: %s", str(ex))
        persistent_notification.create(
            hass,
            f"Error: {ex}<br />You will need to restart hass after fixing.",
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        return

    # non specific repository selected, then show all associated
    if not repositories:
        all_repos = travis.repos(member=user.login)
        repositories = [repo.slug for repo in all_repos]

    entities = []
    monitored_conditions = config[CONF_MONITORED_CONDITIONS]
    for repo in repositories:
        if "/" not in repo:
            repo = f"{user.login}/{repo}"

        entities.extend(
            [
                TravisCISensor(travis, repo, user, branch, description)
                for description in SENSOR_TYPES
                if description.key in monitored_conditions
            ]
        )

    add_entities(entities, True)