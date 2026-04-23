def spawn_program(
    *,
    threads,
    processes,
    first_port,
    addresses,
    process_id,
    repository_url,
    branch,
    program,
    arguments,
    env_base,
):
    temp_root_directory = checkout_repository(repository_url, branch)
    if temp_root_directory is not None:
        repository_path, venv_path = get_temporary_paths(temp_root_directory)
        requirements_path = repository_path / "requirements.txt"
        if program.startswith("python"):
            program = venv_path / "bin" / program
        if requirements_path.exists():
            pip_path = venv_path / "bin" / "pip"
            command = [
                os.fspath(pip_path),
                "install",
                "-r",
                os.fspath(requirements_path),
            ]
            pip_handle = subprocess.run(
                command,
                stderr=subprocess.STDOUT,
            )
            if pip_handle.returncode != 0:
                process_stdout = pip_handle.stdout.decode("utf-8")
                logging.error(f"Failed to install requirements:\n{process_stdout}")
                raise RuntimeError("Failed to install dependencies")
        os.chdir(repository_path)

    run_id = str(uuid.uuid4())
    process_handles = []
    try:
        process_handles = create_process_handles(
            processes=processes,
            threads=threads,
            first_port=first_port,
            addresses=addresses,
            process_id=process_id,
            run_id=run_id,
            program=program,
            arguments=arguments,
            env_base=env_base,
        )
        handles_state = ProcessHandlesState()
        while not handles_state.has_process_with_error:
            handles_state = wait_for_process_handles(process_handles, timeout=1.0)

            if handles_state.needs_upscaling or handles_state.needs_downscaling:
                handles_state.has_process_with_error = False
                terminate_process_handles(process_handles)

                old_process_number = processes
                if handles_state.needs_upscaling:  # Upscaling has bigger priority
                    processes = int(processes * UPSCALING_FACTOR)
                    if processes == old_process_number:
                        processes += 1
                elif handles_state.needs_downscaling:
                    processes = int(processes * DOWNSCALING_FACTOR)
                    if processes == old_process_number:
                        processes -= 1
                    processes = max(processes, 1)
                click.echo(
                    f"Updating the processes number from {old_process_number} to {processes}"
                )

                process_handles = create_process_handles(
                    processes=processes,
                    threads=threads,
                    first_port=first_port,
                    addresses=addresses,
                    run_id=run_id,
                    program=program,
                    arguments=arguments,
                    env_base=env_base,
                )
            elif not handles_state.has_working_process:
                break
    finally:
        terminate_process_handles(process_handles)
    sys.exit(max(handle.returncode for handle in process_handles))