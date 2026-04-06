def get_new_command(command):
    arguments = '-rf'
    if 'hdfs' in command.script:
        arguments = '-r'
    return re.sub('\\brm (.*)', 'rm ' + arguments + ' \\1', command.script)