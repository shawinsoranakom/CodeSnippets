def run_app_server():
    if is_app_server_alive():
        print("Detected React app server already running, won't spawn a new one.")
        return

    env = {
        "BROWSER": "none",  # don't open up chrome, streamlit does this for us
        "BUILD_AS_FAST_AS_POSSIBLE": "true",
        "GENERATE_SOURCEMAP": "false",
        "INLINE_RUNTIME_CHUNK": "false",
    }
    command = ["yarn", "start", "--running-streamlit-e2e-test"]
    proc = AsyncSubprocess(command, cwd=FRONTEND_DIR, env=env)

    print("Starting React app server...")
    proc.start()

    print("Waiting for React app server to come online...")
    start_time = time.time()
    while not is_app_server_alive():
        time.sleep(3)

        # after 10 minutes, we have a problem, just exit
        if time.time() - start_time > 60 * 10:
            print(
                "React app server seems to have had difficulty starting, exiting. Output:"
            )
            print(proc.terminate())
            sys.exit(1)

    print("React app server is alive!")
    return proc