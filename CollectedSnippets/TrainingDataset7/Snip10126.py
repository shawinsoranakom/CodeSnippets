def parse_number(cls, name):
        """
        Given a migration name, try to extract a number from the beginning of
        it. For a squashed migration such as '0001_squashed_0004…', return the
        second number. If no number is found, return None.
        """
        if squashed_match := re.search(r".*_squashed_(\d+)", name):
            return int(squashed_match[1])
        match = re.match(r"^\d+", name)
        if match:
            return int(match[0])
        return None