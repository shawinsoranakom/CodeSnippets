def execute(self, cmd: str, timeout: int | None = None) -> tuple[int, str]:
        timeout = timeout if timeout is not None else self.config.timeout

        # E2B code-interpreter uses commands.run()
        try:
            result = self.sandbox.commands.run(cmd)
            output = ""
            if hasattr(result, 'stdout') and result.stdout:
                output += result.stdout
            if hasattr(result, 'stderr') and result.stderr:
                output += result.stderr
            exit_code = getattr(result, 'exit_code', 0) or 0
            return exit_code, output
        except TimeoutException:
            logger.debug("Command timed out")
            return -1, f'Command: "{cmd}" timed out'
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return -1, str(e)