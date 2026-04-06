def get_new_command(command):
    # Find the argument that is the package name
    for script_part in command.script_parts:
        if (
            script_part not in ["choco", "cinst", "install"]
            # Need exact match (bc chocolatey is a package)
            and not script_part.startswith('-')
            # Leading hyphens are parameters; some packages contain them though
            and '=' not in script_part and '/' not in script_part
            # These are certainly parameters
        ):
            return command.script.replace(script_part, script_part + ".install")
    return []