def handle_command_def(self, line):
        """Handles one command line during command list definition."""
        cmd, arg, line = self.parseline(line)
        if not cmd:
            return False
        if cmd == 'end':
            return True  # end of cmd list
        elif cmd == 'EOF':
            self.message('')
            return True  # end of cmd list
        cmdlist = self.commands[self.commands_bnum]
        if cmd == 'silent':
            cmdlist.append('_pdbcmd_silence_frame_status')
            return False  # continue to handle other cmd def in the cmd list
        if arg:
            cmdlist.append(cmd+' '+arg)
        else:
            cmdlist.append(cmd)
        # Determine if we must stop
        try:
            func = getattr(self, 'do_' + cmd)
        except AttributeError:
            func = self.default
        # one of the resuming commands
        if func.__name__ in self.commands_resuming:
            return True
        return False