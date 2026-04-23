def _read_docker_cli_env_file(env_file: str) -> dict[str, str]:
        """
        Read an environment file in docker CLI format, specified here:
        https://docs.docker.com/reference/cli/docker/container/run/#env
        :param env_file: Path to the environment file
        :return: Read environment variables
        """
        env_vars = {}
        try:
            with open(env_file) as f:
                env_file_lines = f.readlines()
        except FileNotFoundError as e:
            LOG.error(
                "Specified env file '%s' not found. Please make sure the file is properly mounted into the LocalStack container. Error: %s",
                env_file,
                e,
            )
            raise
        except OSError as e:
            LOG.error(
                "Could not read env file '%s'. Please make sure the LocalStack container has the permissions to read it. Error: %s",
                env_file,
                e,
            )
            raise
        for idx, line in enumerate(env_file_lines):
            line = line.strip()
            if not line or line.startswith("#"):
                # skip comments or empty lines
                continue
            lhs, separator, rhs = line.partition("=")
            if rhs or separator:
                env_vars[lhs] = rhs
            else:
                # No "=" in the line, only the name => lookup in local env
                if env_value := os.environ.get(lhs):
                    env_vars[lhs] = env_value
        return env_vars