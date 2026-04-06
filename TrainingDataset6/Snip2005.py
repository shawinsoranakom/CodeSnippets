def match(command):
    return ('push' in command.script and
            '! [rejected]' in command.output and
            'failed to push some refs to' in command.output and
            ('Updates were rejected because the tip of your'
             ' current branch is behind' in command.output or
             'Updates were rejected because the remote '
             'contains work that you do' in command.output))