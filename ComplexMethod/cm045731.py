def get_pw_program_run_time(
    *,
    n_threads,
    n_processes,
    input_path,
    output_path,
    pstorage_path,
    mode,
    pstorage_type,
    persistence_mode,
    first_port,
):
    needs_pw_program_launch = True
    n_retries = 0
    while needs_pw_program_launch:
        needs_pw_program_launch = False
        time_start = time.time()
        process_handles = start_pw_computation(
            n_threads=n_threads,
            n_processes=n_processes,
            input_path=input_path,
            output_path=output_path,
            pstorage_path=pstorage_path,
            mode=mode,
            pstorage_type=pstorage_type,
            persistence_mode=persistence_mode,
            first_port=first_port,
        )
        try:
            needs_polling = mode == STREAMING_MODE_NAME
            while needs_polling:
                print("Waiting for 10 seconds...")
                time.sleep(10)

                # Insert file size check here

                try:
                    modified_at = os.path.getmtime(output_path)
                    file_size = os.path.getsize(output_path)
                    if file_size == 0:
                        continue
                except FileNotFoundError:
                    if time.time() - time_start > 180:
                        raise
                    continue
                if modified_at > time_start and time.time() - modified_at > 60:
                    for process_handle in process_handles:
                        process_handle.kill()
                    needs_polling = False
        finally:
            pw_exit_code = 0
            for process_handle in process_handles:
                if mode == STATIC_MODE_NAME:
                    try:
                        local_exit_code = process_handle.wait(timeout=600)
                    except subprocess.TimeoutExpired:
                        process_handle.kill()
                        local_exit_code = 255
                else:
                    local_exit_code = process_handle.poll()
                    if local_exit_code is None:
                        # In streaming mode the code never ends, so it's the expected
                        # behavior
                        process_handle.kill()
                        local_exit_code = 0
                pw_exit_code = max(pw_exit_code, local_exit_code)

            if pw_exit_code is not None and pw_exit_code != 0:
                warnings.warn(
                    f"Warning: pw program terminated with non zero exit code: {pw_exit_code}"
                )
                assert n_retries < 3, "Number of retries for S3 reconnection exceeded"
                needs_pw_program_launch = True
                n_retries += 1

    return time.time() - time_start