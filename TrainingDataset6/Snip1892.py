def match(command):
    return (
        "No such file or directory" in command.output
        or command.output.startswith("cp: directory")
        and command.output.rstrip().endswith("does not exist")
    )