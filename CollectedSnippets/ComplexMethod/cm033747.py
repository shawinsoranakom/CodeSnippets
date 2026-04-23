def handle_non_posix_targets(
    mode: TargetMode,
    options: LegacyHostOptions,
    targets: list[HostConfig],
) -> list[HostConfig]:
    """Return a list of non-POSIX targets if the target mode is non-POSIX."""
    if mode == TargetMode.WINDOWS_INTEGRATION:
        if options.windows:
            names = resolve_windows_names(options.windows)
            targets = [WindowsRemoteConfig(name=name, provider=options.remote_provider, arch=options.remote_arch) for name in names]
        else:
            targets = [WindowsInventoryConfig(path=options.inventory)]
    elif mode == TargetMode.NETWORK_INTEGRATION:
        if options.platform:
            network_targets = [NetworkRemoteConfig(name=platform, provider=options.remote_provider, arch=options.remote_arch) for platform in options.platform]

            for platform, collection in options.platform_collection or []:
                for entry in network_targets:
                    if entry.platform == platform:
                        entry.collection = collection

            for platform, connection in options.platform_connection or []:
                for entry in network_targets:
                    if entry.platform == platform:
                        entry.connection = connection

            targets = t.cast(list[HostConfig], network_targets)
        else:
            targets = [NetworkInventoryConfig(path=options.inventory)]

    return targets