async def cleanup(self):
        """Cleanup browser process and temporary directory"""
        # Set shutting_down flag BEFORE any termination actions
        self.shutting_down = True

        if self.browser_process:
            try:
                # For builtin browsers that should persist, we should check if it's a detached process
                # Only terminate if we have proper control over the process
                if not self.browser_process.poll():
                    # Process is still running
                    self.browser_process.terminate()
                    # Wait for process to end gracefully
                    for _ in range(10):  # 10 attempts, 100ms each
                        if self.browser_process.poll() is not None:
                            break
                        await asyncio.sleep(0.1)

                    # Force kill if still running
                    if self.browser_process.poll() is None:
                        if sys.platform == "win32":
                            # On Windows, use taskkill /T to kill the entire process tree
                            try:
                                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.browser_process.pid)])
                            except Exception:
                                self.browser_process.kill()
                        else:
                            # On Unix, kill entire process group to reap child processes
                            try:
                                os.killpg(os.getpgid(self.browser_process.pid), signal.SIGKILL)
                            except (ProcessLookupError, OSError):
                                pass
                        await asyncio.sleep(0.1)  # Brief wait for kill to take effect

            except Exception as e:
                self.logger.error(
                    message="Error terminating browser: {error}",
                    tag="ERROR", 
                    params={"error": str(e)},
                )

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.logger.error(
                    message="Error removing temporary directory: {error}",
                    tag="ERROR",
                    params={"error": str(e)},
                )