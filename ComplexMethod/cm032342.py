async def execute_code(req: CodeExecutionRequest):
    language = req.language
    container = await allocate_container_blocking(language)
    if not container:
        return CodeExecutionResult(
            status=ResultStatus.PROGRAM_RUNNER_ERROR,
            stdout="",
            stderr="Container pool is busy",
            exit_code=-10,
            detail="no_available_container",
        )

    task_id = str(uuid.uuid4())
    workdir = f"/tmp/sandbox_{task_id}"
    os.makedirs(workdir, mode=0o700, exist_ok=True)

    try:
        bundle = _build_execution_bundle(req, workdir)
        code_name = str(bundle["code_name"])
        runner_name = str(bundle["runner_name"])

        code_path = os.path.join(workdir, code_name)
        with open(code_path, "wb") as f:
            f.write(bundle["code_bytes"])

        runner_path = os.path.join(workdir, runner_name)
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(str(bundle["runner_source"]))

        args_path = os.path.join(workdir, str(bundle["args_name"]))
        with open(args_path, "w", encoding="utf-8") as f:
            f.write(str(bundle["args_source"]))

        returncode, _, stderr = await async_run_command("docker", "exec", container, "mkdir", "-p", f"/workspace/{task_id}", timeout=5)
        if returncode != 0:
            raise RuntimeError(f"Directory creation failed: {stderr}")

        tar_proc = await asyncio.create_subprocess_exec(
            "tar", "czf", "-", "-C", workdir, code_name, runner_name, str(bundle["args_name"]), stdout=asyncio.subprocess.PIPE
        )
        tar_stdout, _ = await tar_proc.communicate()

        docker_proc = await asyncio.create_subprocess_exec(
            "docker", "exec", "-i", container, "tar", "xzf", "-", "-C", f"/workspace/{task_id}", stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await docker_proc.communicate(input=tar_stdout)

        if docker_proc.returncode != 0:
            raise RuntimeError(stderr.decode())

        start_time = time.time()
        try:
            arguments = req.arguments or {}
            logger.info("Passed in args keys=%s size_bytes=%s", list(arguments.keys()), len(json.dumps(arguments, ensure_ascii=False).encode("utf-8")))
            run_args = _build_container_run_args(language=language, task_id=task_id, container=container, runner_name=runner_name)

            returncode, stdout, stderr = await async_run_command(
                *run_args,
                timeout=TIMEOUT + 5,
            )

            time_used_ms = (time.time() - start_time) * 1000

            logger.info("----------------------------------------------")
            logger.info(f"Code: {str(base64.b64decode(req.code_b64))}")
            logger.info(f"{returncode=}")
            logger.info(f"{stdout=}")
            logger.info(f"{stderr=}")

            if returncode == 0:
                clean_stdout, structured_result = _extract_result_envelope(stdout)
                artifacts = await _collect_artifacts(container, task_id, workdir)
                return CodeExecutionResult(
                    status=ResultStatus.SUCCESS,
                    stdout=clean_stdout,
                    stderr=stderr,
                    exit_code=0,
                    time_used_ms=time_used_ms,
                    artifacts=artifacts,
                    result=structured_result,
                )
            elif returncode == 124:
                return CodeExecutionResult(
                    status=ResultStatus.RESOURCE_LIMIT_EXCEEDED,
                    stdout="",
                    stderr="Execution timeout",
                    exit_code=-124,
                    resource_limit_type=ResourceLimitType.TIME,
                    time_used_ms=time_used_ms,
                )
            elif returncode == 137:
                return CodeExecutionResult(
                    status=ResultStatus.RESOURCE_LIMIT_EXCEEDED,
                    stdout="",
                    stderr="Memory limit exceeded (killed by OOM)",
                    exit_code=-137,
                    resource_limit_type=ResourceLimitType.MEMORY,
                    time_used_ms=time_used_ms,
                )
            return analyze_error_result(stderr, returncode)

        except asyncio.TimeoutError:
            await async_run_command("docker", "exec", container, "pkill", "-9", language)
            return CodeExecutionResult(
                status=ResultStatus.RESOURCE_LIMIT_EXCEEDED,
                stdout="",
                stderr="Execution timeout",
                exit_code=-1,
                resource_limit_type=ResourceLimitType.TIME,
                time_used_ms=(time.time() - start_time) * 1000,
            )

    except Exception as e:
        logger.error(f"Execution exception: {str(e)}")
        return CodeExecutionResult(status=ResultStatus.PROGRAM_RUNNER_ERROR, stdout="", stderr=str(e), exit_code=-3, detail="internal_error")

    finally:
        cleanup_tasks = [async_run_command("docker", "exec", container, "rm", "-rf", f"/workspace/{task_id}"), async_run_command("rm", "-rf", workdir)]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        await release_container(container, language)