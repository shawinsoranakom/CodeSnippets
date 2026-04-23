def split(s):
            open_to_close = {"{": "}", "(": ")", "[": "]"}
            break_idxs = [-1]
            curr_brackets = []
            for i, c in enumerate(s):
                if c in open_to_close:
                    curr_brackets.append(c)
                elif c in open_to_close.values():
                    if not curr_brackets or open_to_close[curr_brackets[-1]] != c:
                        raise AssertionError(
                            f"ERROR: not able to parse the string! Mismatched bracket '{c}'"
                        )
                    curr_brackets.pop()
                elif c == "," and (not curr_brackets):
                    break_idxs.append(i)
            break_idxs.append(len(s))
            out = []
            for i in range(len(break_idxs) - 1):
                start, end = break_idxs[i], break_idxs[i + 1]
                out.append(s[start + 1 : end])
            return out