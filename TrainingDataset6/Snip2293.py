def _get_history_line(self, command_script):
        return u': {}:0;{}\n'.format(int(time()), command_script)