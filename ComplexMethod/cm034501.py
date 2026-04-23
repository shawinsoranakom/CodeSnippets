def _parse(self, line, raise_if_invalid_or_disabled=False):
        valid = False
        enabled = True
        source = ''
        comment = ''

        line = line.strip()
        if line.startswith('#'):
            enabled = False
            line = line[1:]

        # Check for another "#" in the line and treat a part after it as a comment.
        i = line.find('#')
        if i > 0:
            comment = line[i + 1:].strip()
            line = line[:i]

        # Split a source into substring to make sure that it is source spec.
        # Duplicated whitespaces in a valid source spec will be removed.
        source = line.strip()
        if source:
            chunks = source.split()
            if chunks[0] in VALID_SOURCE_TYPES:
                valid = True
                source = ' '.join(chunks)

        if raise_if_invalid_or_disabled and (not valid or not enabled):
            raise InvalidSource(line)

        return valid, enabled, source, comment