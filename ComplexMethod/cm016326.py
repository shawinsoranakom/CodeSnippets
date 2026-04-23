def decorators() -> Iterator[str]:
        rev = reversed(range(block_start))
        newlines = (i for i in rev if tokens[i].type == token.NEWLINE)
        it = iter(itertools.chain(newlines, [-1]))
        # The -1 accounts for the very first line in the file

        end = next(it, -1)  # Like itertools.pairwise in Python 3.10
        for begin in it:
            for i in range(begin + 1, end):
                t = tokens[i]
                if t.type == token.OP and t.string == "@":
                    useful = (t for t in tokens[i:end] if t.type not in _IGNORE)
                    yield "".join(s.string.strip("\n") for s in useful)
                    break
                elif t.type not in _IGNORE:
                    return  # A statement means no more decorators
            end = begin