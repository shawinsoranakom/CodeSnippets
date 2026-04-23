def cloud_init(args: IntegrationConfig, targets: tuple[IntegrationTarget, ...]) -> None:
    """Initialize cloud plugins for the given targets."""
    if args.metadata.cloud_config is not None:
        return  # cloud configuration already established prior to delegation

    args.metadata.cloud_config = {}

    results = {}

    for provider in get_cloud_providers(args, targets):
        if args.prime_containers and not provider.uses_docker:
            continue

        args.metadata.cloud_config[provider.platform] = {}

        start_time = time.time()
        provider.setup()
        end_time = time.time()

        results[provider.platform] = dict(
            platform=provider.platform,
            setup_seconds=int(end_time - start_time),
            targets=[target.name for target in targets],
        )

    if not args.explain and results:
        result_name = '%s-%s.json' % (
            args.command, re.sub(r'[^0-9]', '-', str(datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0, tzinfo=None))))

        data = dict(
            clouds=results,
        )

        write_json_test_results(ResultType.DATA, result_name, data)