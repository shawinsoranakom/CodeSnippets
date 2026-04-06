def get_new_command(command):
    return re.findall(r'^ +(git push [^\s]+ [^\s]+)', command.output, re.MULTILINE)[0]