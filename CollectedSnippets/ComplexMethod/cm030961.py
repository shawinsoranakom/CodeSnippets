def has_remote_subprocess_debugging():
    """Check if we have permissions to debug subprocesses remotely.

    Returns True if we have permissions, False if we don't.
    Checks for:
    - Platform support (Linux, macOS, Windows only)
    - On Linux: process_vm_readv support
    - _remote_debugging module availability
    - Actual subprocess debugging permissions (e.g., macOS entitlements)
    Result is cached.
    """
    # Check platform support
    if sys.platform not in ("linux", "darwin", "win32"):
        return False

    try:
        import _remote_debugging
    except ImportError:
        return False

    # On Linux, check for process_vm_readv support
    if sys.platform == "linux":
        if not getattr(_remote_debugging, "PROCESS_VM_READV_SUPPORTED", False):
            return False

    # First check if we can read our own process
    if not _remote_debugging.is_python_process(os.getpid()):
        return False

    # Check subprocess access - debugging child processes may require
    # additional permissions depending on platform security settings
    import socket
    import subprocess

    # Create a socket for child to signal readiness
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    # Child connects to signal it's ready, then waits for parent to close
    child_code = f"""
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", {port}))
s.recv(1)  # Wait for parent to signal done
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", child_code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        server.settimeout(5.0)
        conn, _ = server.accept()
        # Child is ready, test if we can probe it
        result = _remote_debugging.is_python_process(proc.pid)
        # Check if subprocess is still alive after probing
        if proc.poll() is not None:
            return False
        conn.close()  # Signal child to exit
        return result
    except (socket.timeout, OSError):
        return False
    finally:
        server.close()
        proc.kill()
        proc.wait()