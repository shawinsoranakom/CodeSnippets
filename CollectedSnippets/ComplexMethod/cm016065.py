def _output_csv(self, filename, headers, row):
        if os.path.exists(filename):
            with open(filename) as fd:
                lines = list(csv.reader(fd)) or [[]]
                if headers and len(headers) > len(lines[0]):
                    # if prior results failed the header might not be filled in yet
                    lines[0] = headers
                else:
                    headers = lines[0]
        else:
            lines = [headers]
        lines.append([(f"{x:.6f}" if isinstance(x, float) else x) for x in row])
        with open(filename, "w") as fd:
            writer = csv.writer(fd, lineterminator="\n")
            for line in lines:
                writer.writerow(list(line) + ["0"] * (len(headers) - len(line)))