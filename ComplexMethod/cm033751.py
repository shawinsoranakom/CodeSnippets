def parse(self, state: ParserState) -> str:
        """Parse the input from the given state and return the result."""
        if state.mode == ParserMode.PARSE:
            path = AnyParser().parse(state)

            if not os.path.isfile(path):
                raise ParserError(f'Not a file: {path}')
        else:
            path = ''

            with state.delimit(PATH_DELIMITER, required=False) as boundary:  # type: ParserBoundary
                while boundary.ready:
                    directory = path or '.'

                    try:
                        with os.scandir(directory) as scan:  # type: c.Iterator[os.DirEntry]
                            choices = [f'{item.name}{PATH_DELIMITER}' if item.is_dir() else item.name for item in scan]
                    except OSError:
                        choices = []

                    if not path:
                        choices.append(PATH_DELIMITER)  # allow absolute paths
                        choices.append('../')  # suggest relative paths

                    part = RelativePathNameParser(choices).parse(state)
                    path += f'{part}{boundary.match or ""}'

        return path