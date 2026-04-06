def get_new_command(command):
    option = re.findall(r" -[dfqrstuv]", command.script)[0]
    return re.sub(option, option.upper(), command.script)