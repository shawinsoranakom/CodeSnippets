def _resolve_ignored(ignored):
    if isinstance(ignored, str):
        ignored = [ignored]
    for raw in ignored:
        if isinstance(raw, str):
            if raw.startswith('|'):
                yield raw[1:]
            elif raw.startswith('<') and raw.endswith('>'):
                filename = raw[1:-1]
                try:
                    infile = open(filename)
                except Exception as exc:
                    logger.error(f'ignore file failed: {exc}')
                    continue
                logger.log(1, f'reading ignored names from {filename!r}')
                with infile:
                    for line in infile:
                        if not line:
                            continue
                        if line[0].isspace():
                            continue
                        line = line.partition('#')[0].rstrip()
                        if line:
                            # XXX Recurse?
                            yield line
            else:
                raw = raw.strip()
                if raw:
                    yield raw
        else:
            raise NotImplementedError