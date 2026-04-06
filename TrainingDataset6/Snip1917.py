def get_new_command(command):
    '''
    Prepends docker container rm -f {container ID} to
    the previous docker image rm {image ID} command
    '''
    container_id = command.output.strip().split(' ')
    return shell.and_('docker container rm -f {}', '{}').format(container_id[-1], command.script)