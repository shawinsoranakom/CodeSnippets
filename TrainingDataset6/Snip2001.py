def match(command):
    return "push" in command.script and "The upstream branch of your current branch does not match" in command.output