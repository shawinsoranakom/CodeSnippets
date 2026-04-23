async def _execute_on_e2b(
        self,
        sandbox: AsyncSandbox,
        command: str,
        timeout: int,
        session_id: str | None,
        user_id: str | None = None,
    ) -> ToolResponseBase:
        """Execute *command* on the E2B sandbox via commands.run().

        Integration tokens (e.g. GH_TOKEN) are injected into the sandbox env
        for any user with connected accounts. E2B has full internet access, so
        CLI tools like ``gh`` work without manual authentication.
        """
        envs: dict[str, str] = {
            "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        }
        # Collect injected secret values so we can scrub them from output.
        secret_values: list[str] = []
        if user_id is not None:
            integration_env = await get_integration_env_vars(user_id)
            secret_values = [v for v in integration_env.values() if v]
            envs.update(integration_env)

            # Set git author/committer identity from the user's GitHub profile
            # so commits made in the sandbox are attributed correctly.
            git_identity = await get_github_user_git_identity(user_id)
            if git_identity:
                envs.update(git_identity)

        try:
            result = await sandbox.commands.run(
                f"bash -c {shlex.quote(command)}",
                cwd=E2B_WORKDIR,
                timeout=timeout,
                envs=envs,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            # Scrub injected tokens from command output to prevent exfiltration
            # via `echo $GH_TOKEN`, `env`, `printenv`, etc.
            for secret in secret_values:
                stdout = stdout.replace(secret, "[REDACTED]")
                stderr = stderr.replace(secret, "[REDACTED]")
            return BashExecResponse(
                message=f"Command executed with status code {result.exit_code}",
                stdout=stdout,
                stderr=stderr,
                exit_code=result.exit_code,
                timed_out=False,
                session_id=session_id,
            )
        except Exception as exc:
            if isinstance(exc, TimeoutException):
                return BashExecResponse(
                    message="Execution timed out",
                    stdout="",
                    stderr=f"Timed out after {timeout}s",
                    exit_code=-1,
                    timed_out=True,
                    session_id=session_id,
                )
            logger.error("[E2B] bash_exec failed: %s", exc, exc_info=True)
            return ErrorResponse(
                message=f"E2B execution failed: {exc}",
                error="e2b_execution_error",
                session_id=session_id,
            )