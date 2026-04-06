def get_new_command(command):
    return re.findall('Run heroku _ to run ([^.]*)', command.output)[0]