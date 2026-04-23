def get_command_matches(string: str) -> list[re.Match]:
        # Lump together adjacent brace pairs
        pattern = re.compile(r"""
            (?P<command>\\(?:[a-zA-Z]+|.))
            |(?P<open>{+)
            |(?P<close>}+)
        """, flags=re.X | re.S)
        result = []
        open_stack = []
        for match_obj in pattern.finditer(string):
            if match_obj.group("open"):
                open_stack.append((match_obj.span(), len(result)))
            elif match_obj.group("close"):
                close_start, close_end = match_obj.span()
                while True:
                    if not open_stack:
                        raise ValueError("Missing '{' inserted")
                    (open_start, open_end), index = open_stack.pop()
                    n = min(open_end - open_start, close_end - close_start)
                    result.insert(index, pattern.fullmatch(
                        string, pos=open_end - n, endpos=open_end
                    ))
                    result.append(pattern.fullmatch(
                        string, pos=close_start, endpos=close_start + n
                    ))
                    close_start += n
                    if close_start < close_end:
                        continue
                    open_end -= n
                    if open_start < open_end:
                        open_stack.append(((open_start, open_end), index))
                    break
            else:
                result.append(match_obj)
        if open_stack:
            raise ValueError("Missing '}' inserted")
        return result