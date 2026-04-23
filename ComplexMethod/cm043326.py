async def kill_builtin_browser(self) -> bool:
        """
        Kill the builtin browser if it's running.

        Returns:
            bool: True if the browser was killed, False otherwise
        """
        browser_info = self.get_builtin_browser_info()
        if not browser_info:
            self.logger.warning("No builtin browser found", tag="BUILTIN")
            return False

        pid = browser_info.get('pid')
        if not pid:
            return False

        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
            else:
                os.kill(pid, signal.SIGTERM)
                # Wait for termination
                for _ in range(5):
                    if not self._is_browser_running(pid):
                        break
                    await asyncio.sleep(0.5)
                else:
                    # Force kill if still running
                    os.kill(pid, signal.SIGKILL)

            # Remove config file
            if os.path.exists(self.builtin_config_file):
                os.unlink(self.builtin_config_file)

            self.logger.success("Builtin browser terminated", tag="BUILTIN")
            return True
        except Exception as e:
            self.logger.error(f"Error killing builtin browser: {str(e)}", tag="BUILTIN")
            return False