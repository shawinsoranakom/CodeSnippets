def parse_line(fp):
        for line in fp:
            if isinstance(line, bytes):
                line = line.decode("UTF-8")
            if "warnings summary (final)" in line:
                continue
            # This means we are outside the body of a warning
            elif not line.startswith(" "):
                # process a single warning and move it to `selected_warnings`.
                if len(buffer) > 0:
                    warning = "\n".join(buffer)
                    # Only keep the warnings specified in `targets`
                    if any(f": {x}: " in warning for x in targets):
                        selected_warnings.add(warning)
                    buffer.clear()
                continue
            else:
                line = line.strip()
                buffer.append(line)