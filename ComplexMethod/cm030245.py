def _guess_delimiter(self, data, delimiters):
        """
        The delimiter /should/ occur the same number of times on
        each row. However, due to malformed data, it may not. We don't want
        an all or nothing approach, so we allow for small variations in this
        number.
          1) build a table of the frequency of each character on every line.
          2) build a table of frequencies of this frequency (meta-frequency?),
             e.g.  'x occurred 5 times in 10 rows, 6 times in 1000 rows,
             7 times in 2 rows'
          3) use the mode of the meta-frequency to determine the /expected/
             frequency for that character
          4) find out how often the character actually meets that goal
          5) the character that best meets its goal is the delimiter
        For performance reasons, the data is evaluated in chunks, so it can
        try and evaluate the smallest portion of the data possible, evaluating
        additional chunks as necessary.
        """
        from collections import Counter, defaultdict

        data = list(filter(None, data.split('\n')))

        # build frequency tables
        chunkLength = min(10, len(data))
        iteration = 0
        num_lines = 0
        # {char -> {count_per_line -> num_lines_with_that_count}}
        char_frequency = defaultdict(Counter)
        modes = {}
        delims = {}
        start, end = 0, chunkLength
        while start < len(data):
            iteration += 1
            for line in data[start:end]:
                num_lines += 1
                for char, count in Counter(line).items():
                    if char.isascii():
                        char_frequency[char][count] += 1

            for char, counts in char_frequency.items():
                items = list(counts.items())
                missed_lines = num_lines - sum(counts.values())
                if missed_lines:
                    # Store the number of lines 'char' was missing from.
                    items.append((0, missed_lines))
                if len(items) == 1 and items[0][0] == 0:
                    continue
                # get the mode of the frequencies
                if len(items) > 1:
                    modes[char] = max(items, key=lambda x: x[1])
                    # adjust the mode - subtract the sum of all
                    # other frequencies
                    items.remove(modes[char])
                    modes[char] = (modes[char][0], modes[char][1]
                                   - sum(item[1] for item in items))
                else:
                    modes[char] = items[0]

            # build a list of possible delimiters
            modeList = modes.items()
            total = float(min(chunkLength * iteration, len(data)))
            # (rows of consistent data) / (number of rows) = 100%
            consistency = 1.0
            # minimum consistency threshold
            threshold = 0.9
            while len(delims) == 0 and consistency >= threshold:
                for k, v in modeList:
                    if v[0] > 0 and v[1] > 0:
                        if ((v[1]/total) >= consistency and
                            (delimiters is None or k in delimiters)):
                            delims[k] = v
                consistency -= 0.01

            if len(delims) == 1:
                delim = list(delims.keys())[0]
                skipinitialspace = (data[0].count(delim) ==
                                    data[0].count("%c " % delim))
                return (delim, skipinitialspace)

            # analyze another chunkLength lines
            start = end
            end += chunkLength

        if not delims:
            return ('', 0)

        # if there's more than one, fall back to a 'preferred' list
        if len(delims) > 1:
            for d in self.preferred:
                if d in delims.keys():
                    skipinitialspace = (data[0].count(d) ==
                                        data[0].count("%c " % d))
                    return (d, skipinitialspace)

        # nothing else indicates a preference, pick the character that
        # dominates(?)
        items = [(v,k) for (k,v) in delims.items()]
        items.sort()
        delim = items[-1][1]

        skipinitialspace = (data[0].count(delim) ==
                            data[0].count("%c " % delim))
        return (delim, skipinitialspace)