def validate_localstack_config(name: str):
    # TODO: separate functionality from CLI output
    #  (use exceptions to communicate errors, and return list of warnings)
    from subprocess import CalledProcessError

    dirname = os.getcwd()
    compose_file_name = name if os.path.isabs(name) else os.path.join(dirname, name)
    warns = []

    # some systems do not have "docker-compose" aliased to "docker compose", and older systems do not have
    # "docker compose" at all. By preferring the old way and falling back on the new, we should get docker compose in
    # any way, if installed
    if is_command_available("docker-compose"):
        compose_command = ["docker-compose"]
    else:
        compose_command = ["docker", "compose"]
    # validating docker-compose file
    cmd = [*compose_command, "-f", compose_file_name, "config"]
    try:
        run(cmd, shell=False, print_error=False)
    except CalledProcessError as e:
        msg = f"{e}\n{to_str(e.output)}".strip()
        raise ValueError(msg)

    import yaml  # keep import here to avoid issues in test Lambdas

    # validating docker-compose variable
    with open(compose_file_name) as file:
        compose_content = yaml.full_load(file)
    services_config = compose_content.get("services", {})
    ls_service_name = [
        name for name, svc in services_config.items() if "localstack" in svc.get("image", "")
    ]
    if not ls_service_name:
        raise Exception(
            'No LocalStack service found in config (looking for image names containing "localstack")'
        )
    if len(ls_service_name) > 1:
        warns.append(f"Multiple candidates found for LocalStack service: {ls_service_name}")
    ls_service_name = ls_service_name[0]
    ls_service_details = services_config[ls_service_name]
    image_name = ls_service_details.get("image", "")
    if image_name.split(":")[0] not in constants.OFFICIAL_IMAGES:
        warns.append(
            f'Using custom image "{image_name}", we recommend using an official image: {constants.OFFICIAL_IMAGES}'
        )

    # prepare config options
    container_name = ls_service_details.get("container_name") or ""
    docker_ports = (port.split(":")[-2] for port in ls_service_details.get("ports", []))
    docker_env = {
        env.split("=")[0]: env.split("=")[1] for env in ls_service_details.get("environment", {})
    }
    edge_port = config.GATEWAY_LISTEN[0].port
    main_container = config.MAIN_CONTAINER_NAME

    # docker-compose file validation cases

    if (main_container not in container_name) and not docker_env.get("MAIN_CONTAINER_NAME"):
        warns.append(
            f'Please use "container_name: {main_container}" or add "MAIN_CONTAINER_NAME" in "environment".'
        )

    def port_exposed(port):
        for exposed in docker_ports:
            if re.match(rf"^([0-9]+-)?{port}(-[0-9]+)?$", exposed):
                return True

    if not port_exposed(edge_port):
        warns.append(
            f"Edge port {edge_port} is not exposed. You may have to add the entry "
            'to the "ports" section of the docker-compose file.'
        )

    # print warning/info messages
    for warning in warns:
        console.print("[yellow]:warning:[/yellow]", warning)
    if not warns:
        return True
    return False