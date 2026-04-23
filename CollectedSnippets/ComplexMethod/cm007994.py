def parse_chapters(name, value, advanced=False):
        parse_timestamp = lambda x: float('inf') if x in ('inf', 'infinite') else parse_duration(x)
        TIMESTAMP_RE = r'''(?x)(?:
            (?P<start_sign>-?)(?P<start>[^-]+)
        )?\s*-\s*(?:
            (?P<end_sign>-?)(?P<end>[^-]+)
        )?'''

        chapters, ranges, from_url = [], [], False
        for regex in value or []:
            if advanced and regex == '*from-url':
                from_url = True
                continue
            elif not regex.startswith('*'):
                try:
                    chapters.append(re.compile(regex))
                except re.error as err:
                    raise ValueError(f'invalid {name} regex "{regex}" - {err}')
                continue

            for range_ in map(str.strip, regex[1:].split(',')):
                mobj = range_ != '-' and re.fullmatch(TIMESTAMP_RE, range_)
                dur = mobj and [parse_timestamp(mobj.group('start') or '0'), parse_timestamp(mobj.group('end') or 'inf')]
                signs = mobj and (mobj.group('start_sign'), mobj.group('end_sign'))

                err = None
                if None in (dur or [None]):
                    err = 'Must be of the form "*start-end"'
                elif not advanced and any(signs):
                    err = 'Negative timestamps are not allowed'
                else:
                    dur[0] *= -1 if signs[0] else 1
                    dur[1] *= -1 if signs[1] else 1
                    if dur[1] == float('-inf'):
                        err = '"-inf" is not a valid end'
                if err:
                    raise ValueError(f'invalid {name} time range "{regex}". {err}')
                ranges.append(dur)

        return chapters, ranges, from_url