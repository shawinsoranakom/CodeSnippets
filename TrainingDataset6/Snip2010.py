def get_new_command(command):
    command_list = ['git rebase --continue', 'git rebase --abort', 'git rebase --skip']
    rm_cmd = command.output.split('\n')[-4]
    command_list.append(rm_cmd.strip())
    return get_close_matches(command.script, command_list, 4, 0)