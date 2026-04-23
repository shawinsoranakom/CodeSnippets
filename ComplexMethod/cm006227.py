def print_banner(host: str, port: int, protocol: str) -> None:
    notices = []
    package_names = []  # Track package names for pip install instructions
    is_pre_release = False  # Track if any package is a pre-release
    package_name = ""

    # Use langflow.utils.version to get the version info
    version_info = get_version_info()
    langflow_version = version_info["version"]
    package_name = version_info["package"]
    is_pre_release |= langflow_is_pre_release(langflow_version)  # Update pre-release status

    notice = build_version_notice(langflow_version, package_name)

    notice = stylize_text(notice, package_name, is_prerelease=is_pre_release)
    if notice:
        notices.append(notice)
    package_names.append(package_name)

    # Generate pip command based on the collected data
    pip_command = generate_pip_command(package_names, is_pre_release)

    # Add pip install command to notices if any package needs an update
    if notices:
        notices.append(f"Run '{pip_command}' to update.")

    [f"[bold]{notice}[/bold]" for notice in notices if notice]
    styled_package_name = stylize_text(
        package_name, package_name, is_prerelease=any("pre-release" in notice for notice in notices)
    )

    title = f"[bold]Welcome to {styled_package_name}[/bold]\n"

    # Use Windows-safe characters to prevent encoding issues
    import platform

    if platform.system() == "Windows":
        github_icon = "*"
        discord_icon = "#"
        arrow = "->"
        status_icon = "[OK]"
    else:
        github_icon = ":star2:"
        discord_icon = ":speech_balloon:"
        arrow = "→"
        status_icon = "🟢"

    info_text = (
        f"{github_icon} GitHub: Star for updates {arrow} https://github.com/langflow-ai/langflow\n"
        f"{discord_icon} Discord: Join for support {arrow} https://discord.com/invite/EqksyE2EX9"
    )
    telemetry_text = (
        (
            "We collect anonymous usage data to improve Langflow.\n"
            "To opt out, set: [bold]DO_NOT_TRACK=true[/bold] in your environment."
        )
        if os.getenv("DO_NOT_TRACK", os.getenv("LANGFLOW_DO_NOT_TRACK", "False")).lower() != "true"
        else (
            "We are [bold]not[/bold] collecting anonymous usage data to improve Langflow.\n"
            "To contribute, set: [bold]DO_NOT_TRACK=false[/bold] in your environment."
        )
    )
    access_host = get_best_access_host(host, port)
    access_link = f"[bold]{status_icon} Open Langflow {arrow}[/bold] [link={protocol}://{access_host}:{port}]{protocol}://{access_host}:{port}[/link]"

    message = f"{title}\n{info_text}\n\n{telemetry_text}\n\n{access_link}"

    # Handle Unicode encoding errors on Windows
    try:
        console.print()  # Add line break before banner
        console.print(Panel.fit(message, border_style="#7528FC", padding=(1, 2)))
    except UnicodeEncodeError:
        # Fallback to a simpler banner without emojis for Windows systems with encoding issues
        fallback_message = (
            f"Welcome to {package_name}\n\n"
            "* GitHub: https://github.com/langflow-ai/langflow\n"
            "# Discord: https://discord.com/invite/EqksyE2EX9\n\n"
            f"{telemetry_text}\n\n"
            f"[OK] Open Langflow -> {protocol}://{access_host}:{port}"
        )
        try:
            console.print()  # Add line break before fallback banner
            console.print(Panel.fit(fallback_message, border_style="#7528FC", padding=(1, 2)))
        except UnicodeEncodeError:
            # Last resort: use logger instead of print
            logger.info(f"Welcome to {package_name}")
            logger.info("GitHub: https://github.com/langflow-ai/langflow")
            logger.info("Discord: https://discord.com/invite/EqksyE2EX9")
            logger.info(f"Open Langflow: {protocol}://{access_host}:{port}")