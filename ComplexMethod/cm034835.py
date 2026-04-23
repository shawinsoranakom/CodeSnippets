def _distil(self):
        self.records = []
        with open(self.filename, "r") as f_object:
            lines = f_object.readlines()
            for line in lines:
                if self.keyword not in line:
                    continue
                try:
                    result = None

                    # Distil the string from a line.
                    line = line.strip()
                    line_words = (
                        line.split(self.separator) if self.separator else line.split()
                    )
                    if args.position:
                        result = line_words[self.position]
                    else:
                        # Distil the string following the keyword.
                        for i in range(len(line_words) - 1):
                            if line_words[i] == self.keyword:
                                result = line_words[i + 1]
                                break

                    # Distil the result from the picked string.
                    if not self.range:
                        result = result[0:]
                    elif _is_number(self.range):
                        result = result[0 : int(self.range)]
                    else:
                        result = result[
                            int(self.range.split(":")[0]) : int(
                                self.range.split(":")[1]
                            )
                        ]
                    self.records.append(float(result))
                except Exception as exc:
                    print(
                        "line is: {}; separator={}; position={}".format(
                            line, self.separator, self.position
                        )
                    )

        print(
            "Extract {} records: separator={}; position={}".format(
                len(self.records), self.separator, self.position
            )
        )