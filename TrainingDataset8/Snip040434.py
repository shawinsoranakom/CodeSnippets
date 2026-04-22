def kill_with_pgrep(search_string):
    result = subprocess.run(
        f"pgrep -f '{search_string}'",
        shell=True,
        universal_newlines=True,
        capture_output=True,
    )

    if result.returncode == 0:
        for pid in result.stdout.split():
            try:
                os.kill(int(pid), signal.SIGTERM)
            except Exception as e:
                print("Failed to kill process", e)