async def get_config_path(client: str) -> Path:
    """Get the configuration file path for a given client and operating system."""
    os_type = platform.system()
    is_wsl = os_type == "Linux" and "microsoft" in platform.uname().release.lower()

    if client.lower() == "cursor":
        return Path.home() / ".cursor" / "mcp.json"
    if client.lower() == "windsurf":
        return Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
    if client.lower() == "claude":
        if os_type == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        if os_type == "Windows" or is_wsl:  # Windows or WSL (Claude runs on Windows host)
            if is_wsl:
                # In WSL, we need to access the Windows APPDATA directory
                try:
                    # First try to get the Windows username
                    proc = await create_subprocess_exec(
                        "/mnt/c/Windows/System32/cmd.exe",
                        "/c",
                        "echo %USERNAME%",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, _stderr = await proc.communicate()

                    if proc.returncode == 0 and stdout.strip():
                        windows_username = stdout.decode().strip()
                        return Path(
                            f"/mnt/c/Users/{windows_username}/AppData/Roaming/Claude/claude_desktop_config.json"
                        )

                    # Fallback: try to find the Windows user directory
                    users_dir = Path("/mnt/c/Users")
                    if users_dir.exists():
                        # Get the first non-system user directory
                        user_dirs = [
                            d
                            for d in users_dir.iterdir()
                            if d.is_dir() and not d.name.startswith(("Default", "Public", "All Users"))
                        ]
                        if user_dirs:
                            return user_dirs[0] / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"

                    if not Path("/mnt/c").exists():
                        msg = "Windows C: drive not mounted at /mnt/c in WSL"
                        raise ValueError(msg)

                    msg = "Could not find valid Windows user directory in WSL"
                    raise ValueError(msg)
                except (OSError, CalledProcessError) as e:
                    await logger.awarning("Failed to determine Windows user path in WSL: %s", str(e))
                    msg = f"Could not determine Windows Claude config path in WSL: {e!s}"
                    raise ValueError(msg) from e
            # Regular Windows
            return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"

        msg = "Unsupported operating system for Claude configuration"
        raise ValueError(msg)

    msg = "Unsupported client"
    raise ValueError(msg)