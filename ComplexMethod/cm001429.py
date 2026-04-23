def execute_python_file(
        self,
        filename: str | Path,
        args: list[str] | None = None,
        timeout: int = 120,
        env_vars: dict[str, str] | None = None,
    ) -> str:
        """Execute a Python file in a Docker container and return the output

        Args:
            filename (Path): The name of the file to execute
            args (list, optional): The arguments with which to run the python script
            timeout (int): Timeout in seconds (default: 120)
            env_vars (dict): Environment variables to set

        Returns:
            str: The output of the file
        """
        if args is None:
            args = []
        logger.info(f"Executing python file '{filename}'")

        if not str(filename).endswith(".py"):
            raise InvalidArgumentError("Invalid file type. Only .py files are allowed.")

        file_path = self.workspace.get_path(filename)
        if not self.workspace.exists(file_path):
            # Mimic the response that you get from the command line to make it
            # intuitively understandable for the LLM
            raise FileNotFoundError(
                f"python: can't open file '{filename}': "
                f"[Errno 2] No such file or directory"
            )

        # Prepare environment variables
        exec_env = os.environ.copy()
        if env_vars:
            exec_env.update(env_vars)

        if we_are_running_in_a_docker_container():
            logger.debug(
                "App is running in a Docker container; "
                f"executing {file_path} directly..."
            )
            with self.workspace.mount() as local_path:
                try:
                    result = subprocess.run(
                        [
                            "python",
                            "-B",
                            str(file_path.relative_to(self.workspace.root)),
                        ]
                        + args,
                        capture_output=True,
                        encoding="utf8",
                        cwd=str(local_path),
                        timeout=timeout,
                        env=exec_env,
                    )
                except subprocess.TimeoutExpired:
                    raise CodeTimeoutError(
                        f"Python execution timed out after {timeout} seconds"
                    )
                if result.returncode == 0:
                    return result.stdout
                else:
                    raise CodeExecutionError(result.stderr)

        logger.debug("App is not running in a Docker container")
        return self._run_python_code_in_docker(file_path, args, timeout, env_vars)