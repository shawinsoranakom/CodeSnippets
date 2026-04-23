async def create_container(name: str, language: SupportLanguage) -> bool:
    """Asynchronously create a container"""
    create_args = [
        "docker",
        "run",
        "-d",
        "--runtime=runsc",
        "--name",
        name,
        "--read-only",
        "--tmpfs",
        "/workspace:rw,exec,size=100M,uid=65534,gid=65534",
        "--tmpfs",
        "/tmp:rw,exec,size=50M",
        "--user",
        "nobody",
        "--workdir",
        "/workspace",
    ]
    if os.getenv("SANDBOX_MAX_MEMORY"):
        memory_limit = os.getenv("SANDBOX_MAX_MEMORY") or "256m"
        if is_valid_memory_limit(memory_limit):
            logger.info(f"SANDBOX_MAX_MEMORY: {os.getenv('SANDBOX_MAX_MEMORY')}")
        else:
            logger.info("Invalid SANDBOX_MAX_MEMORY, using default value: 256m")
            memory_limit = "256m"
        create_args.extend(["--memory", memory_limit])
    else:
        logger.info("Set default SANDBOX_MAX_MEMORY: 256m")
        create_args.extend(["--memory", "256m"])

    if env_setting_enabled("SANDBOX_ENABLE_SECCOMP", "false"):
        logger.info(f"SANDBOX_ENABLE_SECCOMP: {os.getenv('SANDBOX_ENABLE_SECCOMP')}")
        create_args.extend(["--security-opt", "seccomp=/app/seccomp-profile-default.json"])

    if language == SupportLanguage.PYTHON:
        create_args.append(os.getenv("SANDBOX_BASE_PYTHON_IMAGE", "sandbox-base-python:latest"))
    elif language == SupportLanguage.NODEJS:
        create_args.append(os.getenv("SANDBOX_BASE_NODEJS_IMAGE", "sandbox-base-nodejs:latest"))

    logger.info(f"Sandbox config:\n\t {create_args}")

    try:
        return_code, _, stderr = await async_run_command(*create_args, timeout=10)
        if return_code != 0:
            logger.error(f"❌ Container creation failed {name}: {stderr}")
            return False

        if language == SupportLanguage.NODEJS:
            copy_cmd = ["docker", "exec", name, "bash", "-c", "cp -a /app/node_modules /workspace/"]
            return_code, _, stderr = await async_run_command(*copy_cmd, timeout=10)
            if return_code != 0:
                logger.error(f"❌ Failed to prepare dependencies for {name}: {stderr}")
                return False

        return await container_is_running(name)
    except Exception as e:
        logger.error(f"❌ Container creation exception {name}: {str(e)}")
        return False