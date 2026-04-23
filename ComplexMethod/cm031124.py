def test_recursive_child_discovery(self):
        """Test that recursive=True finds grandchildren."""
        # Create a child that spawns a grandchild and keeps a reference to it
        # so we can clean it up via the child process
        code = """
import subprocess
import sys
import threading
grandchild = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
print(grandchild.pid, flush=True)
# Wait for parent to send signal byte (cross-platform)
# Using threading with timeout so test doesn't hang if something goes wrong
# Timeout is 60s (2x test timeout) to ensure child outlives test in worst case
def wait_for_signal():
    try:
        sys.stdin.buffer.read(1)
    except:
        pass
t = threading.Thread(target=wait_for_signal, daemon=True)
t.start()
t.join(timeout=60)
# Clean up grandchild before exiting
if grandchild.poll() is None:
    grandchild.terminate()
    try:
        grandchild.wait(timeout=2)
    except subprocess.TimeoutExpired:
        grandchild.kill()
        try:
            grandchild.wait(timeout=2)
        except subprocess.TimeoutExpired:
            grandchild.wait()
"""
        proc = subprocess.Popen(
            [sys.executable, "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        grandchild_pid = None
        try:
            # Read grandchild PID with thread-based timeout
            # This prevents indefinite blocking on all platforms
            grandchild_pid_line = _readline_with_timeout(
                proc.stdout, SHORT_TIMEOUT
            )
            if grandchild_pid_line is None:
                self.fail(
                    f"Timeout waiting for grandchild PID from child process "
                    f"(child PID: {proc.pid})"
                )
            if not grandchild_pid_line:
                self.fail(
                    f"Child process {proc.pid} closed stdout without printing "
                    f"grandchild PID"
                )
            grandchild_pid = int(grandchild_pid_line.strip())

            # Poll until grandchild is visible
            deadline = time.time() + SHORT_TIMEOUT
            pids_recursive = []
            while time.time() < deadline:
                pids_recursive = get_child_pids(os.getpid(), recursive=True)
                if grandchild_pid in pids_recursive:
                    break
                time.sleep(0.05)

            self.assertIn(
                proc.pid,
                pids_recursive,
                f"Child PID {proc.pid} not found in recursive discovery. "
                f"Found: {pids_recursive}",
            )
            self.assertIn(
                grandchild_pid,
                pids_recursive,
                f"Grandchild PID {grandchild_pid} not found in recursive discovery. "
                f"Found: {pids_recursive}",
            )

            # Non-recursive should find only direct child
            pids_direct = get_child_pids(os.getpid(), recursive=False)
            self.assertIn(
                proc.pid,
                pids_direct,
                f"Child PID {proc.pid} not found in non-recursive discovery. "
                f"Found: {pids_direct}",
            )
            self.assertNotIn(
                grandchild_pid,
                pids_direct,
                f"Grandchild PID {grandchild_pid} should NOT be in non-recursive "
                f"discovery. Found: {pids_direct}",
            )
        finally:
            # Send signal byte to child to trigger cleanup, then close stdin
            try:
                proc.stdin.write(b"x")
                proc.stdin.flush()
                proc.stdin.close()
            except OSError:
                pass
            proc.stdout.close()
            _cleanup_process(proc)
            # The grandchild may not have been cleaned up by the child process
            # (e.g., if the child was killed). Explicitly terminate the
            # grandchild to prevent PermissionError on Windows when removing
            # temp directories.
            if grandchild_pid is not None:
                try:
                    os.kill(grandchild_pid, signal.SIGTERM)
                except (OSError, ProcessLookupError):
                    pass