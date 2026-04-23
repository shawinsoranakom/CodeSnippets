def parse_clinic_block(self, dsl_name: str) -> Block:
        in_lines = []
        self.block_start_line_number = self.line_number + 1
        stop_line = self.language.stop_line.format(dsl_name=dsl_name)
        body_prefix = self.language.body_prefix.format(dsl_name=dsl_name)

        def is_stop_line(line: str) -> bool:
            # make sure to recognize stop line even if it
            # doesn't end with EOL (it could be the very end of the file)
            if line.startswith(stop_line):
                remainder = line.removeprefix(stop_line)
                if remainder and not remainder.isspace():
                    fail(f"Garbage after stop line: {remainder!r}")
                return True
            else:
                # gh-92256: don't allow incorrectly formatted stop lines
                if line.lstrip().startswith(stop_line):
                    fail(f"Whitespace is not allowed before the stop line: {line!r}")
                return False

        # consume body of program
        while self.input:
            line = self._line()
            if is_stop_line(line) or self.is_start_line(line):
                break
            if body_prefix:
                line = line.lstrip()
                assert line.startswith(body_prefix)
                line = line.removeprefix(body_prefix)
            in_lines.append(line)

        # consume output and checksum line, if present.
        if self.last_dsl_name == dsl_name:
            checksum_re = self.last_checksum_re
        else:
            before, _, after = self.language.checksum_line.format(dsl_name=dsl_name, arguments='{arguments}').partition('{arguments}')
            assert _ == '{arguments}'
            checksum_re = libclinic.create_regex(before, after, word=False)
            self.last_dsl_name = dsl_name
            self.last_checksum_re = checksum_re
        assert checksum_re is not None

        # scan forward for checksum line
        out_lines = []
        arguments = None
        while self.input:
            line = self._line(lookahead=True)
            match = checksum_re.match(line.lstrip())
            arguments = match.group(1) if match else None
            if arguments:
                break
            out_lines.append(line)
            if self.is_start_line(line):
                break

        output: str | None
        output = "".join(out_lines)
        if arguments:
            d = {}
            for field in shlex.split(arguments):
                name, equals, value = field.partition('=')
                if not equals:
                    fail(f"Mangled Argument Clinic marker line: {line!r}")
                d[name.strip()] = value.strip()

            if self.verify:
                if 'input' in d:
                    checksum = d['output']
                else:
                    checksum = d['checksum']

                computed = libclinic.compute_checksum(output, len(checksum))
                if checksum != computed:
                    fail("Checksum mismatch! "
                         f"Expected {checksum!r}, computed {computed!r}. "
                         "Suggested fix: remove all generated code including "
                         "the end marker, or use the '-f' option.")
        else:
            # put back output
            output_lines = output.splitlines(keepends=True)
            self.line_number -= len(output_lines)
            self.input.extend(reversed(output_lines))
            output = None

        return Block("".join(in_lines), dsl_name, output=output)