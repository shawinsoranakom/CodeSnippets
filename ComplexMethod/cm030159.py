def precmd(self, line):
        """Handle alias expansion and ';;' separator."""
        if not line.strip():
            return line
        args = line.split()
        while args[0] in self.aliases:
            line = self.aliases[args[0]]
            for idx in range(1, 10):
                if f'%{idx}' in line:
                    if idx >= len(args):
                        self.error(f"Not enough arguments for alias '{args[0]}'")
                        # This is a no-op
                        return "!"
                    line = line.replace(f'%{idx}', args[idx])
                elif '%*' not in line:
                    if idx < len(args):
                        self.error(f"Too many arguments for alias '{args[0]}'")
                        # This is a no-op
                        return "!"
                    break

            line = line.replace("%*", ' '.join(args[1:]))
            args = line.split()
        # split into ';;' separated commands
        # unless it's an alias command
        if args[0] != 'alias':
            marker = line.find(';;')
            if marker >= 0:
                # queue up everything after marker
                next = line[marker+2:].lstrip()
                self.cmdqueue.insert(0, next)
                line = line[:marker].rstrip()

        # Replace all the convenience variables
        line = self._replace_convenience_variables(line)

        return line