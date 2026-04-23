def interact(self):
        self.output.write('\n')
        while True:
            try:
                request = self.getline('help> ')
            except (KeyboardInterrupt, EOFError):
                break
            request = request.strip()
            if not request:
                continue  # back to the prompt

            # Make sure significant trailing quoting marks of literals don't
            # get deleted while cleaning input
            if (len(request) > 2 and request[0] == request[-1] in ("'", '"')
                    and request[0] not in request[1:-1]):
                request = request[1:-1]
            if request.lower() in ('q', 'quit', 'exit'): break
            if request == 'help':
                self.intro()
            else:
                self.help(request)