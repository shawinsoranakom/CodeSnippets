def run(
    image: str = None,
    volume_dir: str = None,
    pro: bool = None,
    develop: bool = False,
    randomize: bool = False,
    mount_source: bool = True,
    live_reload: bool = False,
    mount_dependencies: bool = False,
    mount_entrypoints: bool = False,
    mount_docker_socket: bool = True,
    env: tuple = (),
    volume: tuple = (),
    publish: tuple = (),
    entrypoint: str = None,
    network: str = None,
    local_packages: list[str] | None = None,
    command: str = None,
):
    """
    A tool for localstack developers to start localstack containers. Run this in your localstack or
    localstack-pro source tree to mount local source files or dependencies into the container.
    Here are some examples::

    \b
        python -m localstack.dev.run
        python -m localstack.dev.run -e DEBUG=1 -e LOCALSTACK_AUTH_TOKEN=test
        python -m localstack.dev.run -- bash -c 'echo "hello"'

    Explanations and more examples:

    Start a normal container localstack container. If you run this from the localstack-pro repo,
    it will start localstack-pro::

        python -m localstack.dev.run

    If you start localstack-pro, you might also want to add the API KEY as environment variable::

        python -m localstack.dev.run -e DEBUG=1 -e LOCALSTACK_AUTH_TOKEN=test

    If your local changes are making modifications to plux plugins (e.g., adding new providers or hooks),
    then you also want to mount the newly generated entry_point.txt files into the container::

        python -m localstack.dev.run --mount-entrypoints

    Start a new container with randomized gateway and service ports, and randomized container name::

        python -m localstack.dev.run --randomize

    You can also run custom commands:

        python -m localstack.dev.run bash -c 'echo "hello"'

    Or use custom entrypoints:

        python -m localstack.dev.run --entrypoint /bin/bash -- echo "hello"

    Use the --live-reload flag to restart LocalStack on code changes. Beware: this will remove any state
    that you had in your LocalStack instance. Consider using PERSISTENCE to keep resources:

        python -m localstack.dev.run --live-reload

    You can import and expose debugpy:

        python -m localstack.dev.run --develop

    You can also mount local dependencies (e.g., pytest and other test dependencies, and then use that
    in the container)::

    \b
        python -m localstack.dev.run --mount-dependencies \\
            -v $PWD/tests:/opt/code/localstack/tests \\
            -- .venv/bin/python -m pytest tests/unit/http_/

    The script generally assumes that you are executing in either localstack or localstack-pro source
    repositories that are organized like this::

    \b
        somedir                              <- your workspace directory
        ├── localstack                       <- execute script in here
        │   ├── ...
        │   ├── localstack-core
        │   │   ├── localstack               <- will be mounted into the container
        │   │   └── localstack_core.egg-info
        │   ├── pyproject.toml
        │   ├── tests
        │   └── ...
        ├── localstack-pro                   <- or execute script in here
        │   ├── ...
        │   ├── localstack-pro-core
        │   │   ├── localstack
        │   │   │   └── pro
        │   │   │       └── core             <- will be mounted into the container
        │   │   ├── localstack_ext.egg-info
        │   │   ├── pyproject.toml
        │   │   └── tests
        │   └── ...
        ├── moto
        │   ├── AUTHORS.md
        │   ├── ...
        │   ├── moto                         <- will be mounted into the container
        │   ├── moto_ext.egg-info
        │   ├── pyproject.toml
        │   ├── tests
        │   └── ...

    You can choose which local source repositories are mounted in. For example, if `moto` and `rolo` are
    both present, only mount `rolo` into the container.

    \b
        python -m localstack.dev.run --local-packages rolo

    If both `rolo` and `moto` are available and both should be mounted, use the flag twice.

    \b
        python -m localstack.dev.run --local-packages rolo --local-packages moto
    """
    with console.status("Configuring") as status:
        env_vars = parse_env_vars(env)
        configure_licensing_credentials_environment(env_vars)

        # run all prepare_host hooks
        hooks.prepare_host.run()

        # set the VOLUME_DIR config variable like in the CLI
        if not os.environ.get("LOCALSTACK_VOLUME_DIR", "").strip():
            config.VOLUME_DIR = str(cache_dir() / "volume")

        # setup important paths on the host
        host_paths = HostPaths(
            # we assume that python -m localstack.dev.run is always executed in the repo source
            workspace_dir=os.path.abspath(os.path.join(os.getcwd(), "..")),
            volume_dir=volume_dir or config.VOLUME_DIR,
        )

        # auto-set pro flag
        if pro is None:
            if os.getcwd().endswith("localstack-pro"):
                pro = True
            else:
                pro = False

        # setup base configuration
        container_config = ContainerConfiguration(
            image_name=image,
            name=config.MAIN_CONTAINER_NAME if not randomize else f"localstack-{short_uid()}",
            remove=True,
            interactive=True,
            tty=True,
            env_vars={},
            volumes=VolumeMappings(),
            ports=PortMappings(),
            network=network,
        )

        # replicate pro startup
        if pro:
            try:
                from localstack.pro.core.plugins import modify_gateway_listen_config

                modify_gateway_listen_config(config)
            except ImportError:
                pass

        # setup configurators
        configurators = [
            ImageConfigurator(pro, image),
            PortConfigurator(randomize),
            ConfigEnvironmentConfigurator(pro),
            ContainerConfigurators.mount_localstack_volume(host_paths.volume_dir),
            ContainerConfigurators.config_env_vars,
        ]

        # create stub container with configuration to apply
        c = Container(container_config=container_config)

        # apply existing hooks first that can later be overwritten
        hooks.configure_localstack_container.run(c)

        if command:
            configurators.append(ContainerConfigurators.custom_command(list(command)))
        if entrypoint:
            container_config.entrypoint = entrypoint
        if mount_docker_socket:
            configurators.append(ContainerConfigurators.mount_docker_socket)
        if mount_source:
            configurators.append(
                SourceVolumeMountConfigurator(
                    host_paths=host_paths,
                    pro=pro,
                    chosen_packages=local_packages,
                )
            )
        if mount_entrypoints:
            configurators.append(EntryPointMountConfigurator(host_paths=host_paths, pro=pro))
        if mount_dependencies:
            configurators.append(DependencyMountConfigurator(host_paths=host_paths))
        if develop:
            configurators.append(ContainerConfigurators.develop)

        # make sure anything coming from CLI arguments has priority
        configurators.extend(
            [
                ContainerConfigurators.volume_cli_params(volume),
                ContainerConfigurators.port_cli_params(publish),
                ContainerConfigurators.env_cli_params(env),
            ]
        )

        # run configurators
        for configurator in configurators:
            configurator(container_config)
        # print the config
        print_config(container_config)

        # run the container
        docker = CmdDockerClient()
        status.update("Creating container")
        container_id = docker.create_container_from_config(container_config)

    rule = Rule(f"Interactive session with {container_id[:12]} 💻")
    console.print(rule)
    stop_live_reload_watcher = None
    try:
        if live_reload and mount_source:
            # Some install targets don't include the `watchdog` dependency, and some developers
            # don't install LocalStack using the `Makefile`, so they find that they don't have
            # the `watchdog` dependency. We lazy import these functions so that we don't trigger
            # an import error for these developers.
            from localstack.dev.run.watcher import collect_watch_directories, start_file_watcher

            if watch_dirs := collect_watch_directories(host_paths, pro, local_packages):
                stop_live_reload_watcher = start_file_watcher(watch_dirs, docker, container_id)

        cmd = [*docker._docker_cmd(), "start", "--interactive", "--attach", container_id]
        run_interactive(cmd)
    finally:
        if stop_live_reload_watcher is not None:
            stop_live_reload_watcher.set()

        if container_config.remove:
            try:
                if docker.is_container_running(container_id):
                    docker.stop_container(container_id)
                docker.remove_container(container_id)
            except Exception:
                pass