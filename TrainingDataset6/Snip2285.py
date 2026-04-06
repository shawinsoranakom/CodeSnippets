def _get_history_line(self, command_script):
        return u'#+{}\n{}\n'.format(int(time()), command_script)