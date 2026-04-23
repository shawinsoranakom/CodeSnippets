def run_scenario_in_docker(
    work_dir: str, env: Dict[str, str], timeout: int = TASK_TIMEOUT, docker_image: Optional[str] = None
) -> None:
    """
    Run a scenario in a Docker environment.

    Args:
        work_dir (path): the path to the working directory previously created to house this sceario instance
        timeout (Optional, int): the number of seconds to allow a Docker container to run before timing out
    """

    client = docker.from_env()
    image = None

    # If the docker_image is None, then we will fetch DEFAULT_DOCKER_IMAGE_TAG, if present,
    # or build it if missing.
    if docker_image is None:
        # Pull a suitable image
        try:
            image = client.images.get(DEFAULT_DOCKER_IMAGE_TAG)
        except ImageNotFound:
            print(f"Building default Docker image '{DEFAULT_DOCKER_IMAGE_TAG}'. This may take a few minutes...")
            try:
                build_default_docker_image(client, DEFAULT_DOCKER_IMAGE_TAG)
                image = client.images.get(DEFAULT_DOCKER_IMAGE_TAG)
            except DockerException:
                print(f"Failed to build image '{DEFAULT_DOCKER_IMAGE_TAG}'")

    # Otherwise get the requested image
    else:
        try:
            image = client.images.get(docker_image)
        except ImageNotFound:
            # pull the image
            print(f"Pulling image '{docker_image}'")
            try:
                image = client.images.pull(docker_image)
            except DockerException:
                print(f"Failed to pull image '{docker_image}'")

    # Prepare the run script
    with open(os.path.join(work_dir, "run.sh"), "wt", newline="\n") as f:
        f.write(
            f"""#
echo RUN.SH STARTING !#!#
export AUTOGEN_TESTBED_SETTING="Docker"

umask 000
echo "agbench version: {__version__}" > timestamp.txt

# Run the global init script if it exists
if [ -f global_init.sh ] ; then
    . ./global_init.sh
fi

# Run the scenario init script if it exists
if [ -f scenario_init.sh ] ; then
    . ./scenario_init.sh
fi

# Run the scenario
pip install -r requirements.txt
echo SCENARIO.PY STARTING !#!#
start_time=$(date +%s)
timeout --preserve-status --kill-after {timeout  + 30}s {timeout}s python scenario.py
end_time=$(date +%s)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo SCENARIO.PY EXITED WITH CODE: $EXIT_CODE !#!#
else
    echo SCENARIO.PY COMPLETE !#!#
fi
elapsed_time=$((end_time - start_time))
echo "SCENARIO.PY RUNTIME: $elapsed_time !#!#"

# Clean up
if [ -d .cache ] ; then
    rm -Rf .cache
fi

if [ -d __pycache__ ] ; then
    rm -Rf __pycache__
fi

# Run the scenario finalize script if it exists
if [ -f scenario_finalize.sh ] ; then
    . ./scenario_finalize.sh
fi

# Run the global finalize script if it exists
if [ -f global_finalize.sh ] ; then
    . ./global_finalize.sh
fi

echo RUN.SH COMPLETE !#!#
"""
        )

    # Figure out what folders to mount
    volumes = {str(pathlib.Path(work_dir).absolute()): {"bind": "/workspace", "mode": "rw"}}

    # Add the autogen repo if we can find it
    autogen_repo_base = os.environ.get("AUTOGEN_REPO_BASE")
    if autogen_repo_base is None:
        autogen_repo_base = find_autogen_repo(os.getcwd())
    elif not os.path.isdir(autogen_repo_base):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), autogen_repo_base)

    if autogen_repo_base is None:
        raise ValueError(
            "Could not find AutoGen repo base. Please set the environment variable AUTOGEN_REPO_BASE to the correct value."
        )

    autogen_repo_base = os.path.join(autogen_repo_base, "python")
    volumes[str(pathlib.Path(autogen_repo_base).absolute())] = {"bind": "/autogen_python", "mode": "rw"}

    # Add the Docker socket if we are running on Linux
    # This allows docker-out-of-docker to work, but provides access to the Docker daemon on the host.
    # This maintains good isolation for experiment purposes (e.g., ensuring consistent initial conditions),
    # but deminishes the security benefits of using Docker (e.g., when facing a deliberately malicious agent).
    # since it would allow clients to mount privalaged images, volumes, etc.
    docker_host = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
    if docker_host.startswith("unix://"):
        docker_socket = os.path.abspath(docker_host[7:])
        if os.path.exists(docker_socket):
            st_mode = os.stat(docker_socket).st_mode
            if stat.S_ISSOCK(st_mode):
                volumes[docker_socket] = {"bind": "/var/run/docker.sock", "mode": "rw"}

                # Update the environment variables so that the inner docker client can
                # mount the workspace
                env = {k: v for k, v in env.items()}
                env["HOST_WORKSPACE"] = str(pathlib.Path(work_dir).absolute())

    print("Mounting:")
    for k in volumes.keys():
        bind = volumes[k]["bind"]
        mode = volumes[k]["mode"].upper()
        if bind == "/workspace":
            k = os.path.relpath(k)
        print(f"[{mode}]\t'{k}' => '{bind}'")
    print("===================================================================")

    assert image is not None
    # Create and run the container
    container = client.containers.run(
        image,
        command=["sh", "run.sh"],
        working_dir="/workspace",
        environment=env,
        detach=True,
        remove=True,
        auto_remove=True,
        # Type hint of docker is wrong here
        volumes=volumes,  # type: ignore
        network="host",  # Use the host network to avoid issues with localhost.
    )

    # Read the logs in a streaming fashion. Keep an eye on the time to make sure we don't need to stop.
    docker_timeout: float = timeout + 60  # One full minute after the bash timeout command should have already triggered
    start_time = time.time()
    logs = container.logs(stream=True)
    log_file = open(os.path.join(work_dir, "console_log.txt"), "wt", encoding="utf-8")
    stopping = False
    exiting = False

    while True:
        try:
            chunk = next(logs)  # Manually step the iterator so it is captures with the try-catch

            # Stream the data to the log file and the console
            chunk_str = chunk.decode("utf-8")
            log_file.write(chunk_str)
            log_file.flush()
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
            sys.stdout.write(chunk_str)
            sys.stdout.flush()

            # Check if we need to terminate
            if not stopping and time.time() - start_time >= docker_timeout:
                container.stop()

                # Don't exit the loop right away, as there are things we may still want to read from the logs
                # but remember how we got here.
                stopping = True
        except KeyboardInterrupt:
            log_file.write("\nKeyboard interrupt (Ctrl-C). Attempting to exit gracefully.\n")
            log_file.flush()
            sys.stdout.write("\nKeyboard interrupt (Ctrl-C). Attempting to exit gracefully.\n")
            sys.stdout.flush()

            # Start the exit process, and give it a minute, but keep iterating
            container.stop()
            exiting = True
            docker_timeout = time.time() - start_time + 60
        except StopIteration:
            break

    # Clean up the container
    try:
        container.remove()
    except APIError:
        pass

    if stopping:  # By this line we've exited the loop, and the container has actually stopped.
        log_file.write("\nDocker timed out.\n")
        log_file.flush()
        sys.stdout.write("\nDocker timed out.\n")
        sys.stdout.flush()

    if exiting:  # User hit ctrl-C
        sys.exit(1)