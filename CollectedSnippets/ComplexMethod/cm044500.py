def get_commands() -> list[str]:
    """ Return commands formatted for GUI

    Returns
    -------
    list[str]
        A list of faceswap and tools commands that can be displayed in Faceswap's GUI
    """
    command_path = os.path.join(PROJECT_ROOT, "scripts")
    tools_path = os.path.join(PROJECT_ROOT, "tools")
    commands = [os.path.splitext(item)[0] for item in os.listdir(command_path)
                if os.path.splitext(item)[1] == ".py"
                and os.path.splitext(item)[0] not in ("gui", "fs_media")
                and not os.path.splitext(item)[0].startswith("_")]
    tools = [os.path.splitext(item)[0] for item in os.listdir(tools_path)
             if os.path.splitext(item)[1] == ".py"
             and os.path.splitext(item)[0] not in ("gui", "cli")
             and not os.path.splitext(item)[0].startswith("_")]
    return commands + tools