def run(self, command: str, timeout: Optional[int] = None) -> Tuple[str, str, int]:
        start = time.time()
        print("\n--- Start of run ---")
        # while running, also print the stdout and stderr
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.files.working_dir,
            text=True,
            shell=True,
        )
        print("$", command)
        stdout_full, stderr_full = "", ""

        try:
            while p.poll() is None:
                assert p.stdout is not None
                assert p.stderr is not None
                stdout = p.stdout.readline()
                stderr = p.stderr.readline()
                if stdout:
                    print(stdout, end="")
                    stdout_full += stdout
                if stderr:
                    print(stderr, end="")
                    stderr_full += stderr
                if timeout and time.time() - start > timeout:
                    print("Timeout!")
                    p.kill()
                    raise TimeoutError()
        except KeyboardInterrupt:
            print()
            print("Stopping execution.")
            print("Execution stopped.")
            p.kill()
            print()
            print("--- Finished run ---\n")

        return stdout_full, stderr_full, p.returncode