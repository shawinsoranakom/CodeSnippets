def terminate_tree(proc: subprocess.Popen, timeout = 15):
    if proc is None or proc.poll() is not None:
        return

    try:
        import psutil

        parent = psutil.Process(proc.pid)
        for child in parent.children(recursive = True):
            child.terminate()
        parent.terminate()
        parent.wait(timeout = timeout / 2)
        return
    except:
        pass

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                capture_output = True,
                timeout = 5,
            )
            proc.wait(timeout = 1)
            return
        except:
            pass

    proc.kill()
    try:
        proc.wait(timeout = 5)
    except:
        pass