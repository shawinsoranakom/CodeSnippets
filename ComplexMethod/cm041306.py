def _run_async_cmd(
        self, cmd: list[str], stdin: bytes, container_name: str, image_name=None
    ) -> tuple[bytes, bytes]:
        kwargs = {
            "inherit_env": True,
            "asynchronous": True,
            "stderr": subprocess.PIPE,
            "outfile": self.default_run_outfile or subprocess.PIPE,
        }
        if stdin:
            kwargs["stdin"] = True
        try:
            process = run(cmd, **kwargs)
            stdout, stderr = process.communicate(input=stdin)
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode,
                    cmd,
                    stdout,
                    stderr,
                )
            else:
                return stdout, stderr
        except subprocess.CalledProcessError as e:
            stderr_str = to_str(e.stderr)
            if "Unable to find image" in stderr_str:
                raise NoSuchImage(image_name or "", stdout=e.stdout, stderr=e.stderr)
            # consider different error messages for Docker/Podman
            error_messages = ("No such container", "no container with name or ID")
            if any(msg.lower() in to_str(e.stderr).lower() for msg in error_messages):
                raise NoSuchContainer(container_name, stdout=e.stdout, stderr=e.stderr)
            raise ContainerException(
                f"Docker process returned with errorcode {e.returncode}", e.stdout, e.stderr
            ) from e