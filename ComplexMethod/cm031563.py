def parse(self, lines):
        """Parse the input lines from a robots.txt file.

        We allow that a user-agent: line is not preceded by
        one or more blank lines.
        """
        # states:
        #   0: start state
        #   1: saw user-agent line
        #   2: saw an allow or disallow line
        state = 0
        entry = Entry()

        self.modified()
        for line in lines:
            if not line:
                if state == 1:
                    entry = Entry()
                    state = 0
                elif state == 2:
                    self._add_entry(entry)
                    entry = Entry()
                    state = 0
            # remove optional comment and strip line
            i = line.find('#')
            if i >= 0:
                line = line[:i]
            line = line.strip()
            if not line:
                continue
            line = line.split(':', 1)
            if len(line) == 2:
                line[0] = line[0].strip().lower()
                line[1] = line[1].strip()
                if line[0] == "user-agent":
                    if state == 2:
                        self._add_entry(entry)
                        entry = Entry()
                    entry.useragents.append(line[1])
                    state = 1
                elif line[0] == "disallow":
                    if state != 0:
                        entry.rulelines.append(RuleLine(line[1], False))
                        state = 2
                elif line[0] == "allow":
                    if state != 0:
                        entry.rulelines.append(RuleLine(line[1], True))
                        state = 2
                elif line[0] == "crawl-delay":
                    if state != 0:
                        # before trying to convert to int we need to make
                        # sure that robots.txt has valid syntax otherwise
                        # it will crash
                        if line[1].strip().isdigit():
                            entry.delay = int(line[1])
                        state = 2
                elif line[0] == "request-rate":
                    if state != 0:
                        numbers = line[1].split('/')
                        # check if all values are sane
                        if (len(numbers) == 2 and numbers[0].strip().isdigit()
                            and numbers[1].strip().isdigit()):
                            entry.req_rate = RequestRate(int(numbers[0]), int(numbers[1]))
                        state = 2
                elif line[0] == "sitemap":
                    # According to http://www.sitemaps.org/protocol.html
                    # "This directive is independent of the user-agent line,
                    #  so it doesn't matter where you place it in your file."
                    # Therefore we do not change the state of the parser.
                    self.sitemaps.append(line[1])
        if state == 2:
            self._add_entry(entry)