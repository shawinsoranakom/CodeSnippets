def _separate_at_op(self, expr, max_split=None):

        for op, _ in self._all_operators():
            # hackety: </> have higher priority than <</>>, but don't confuse them
            skip_delim = (op + op) if op in '<>*?' else None
            if op == '?':
                skip_delim = (skip_delim, '?.')
            separated = list(self._separate(expr, op, skip_delims=skip_delim))
            if len(separated) < 2:
                continue

            right_expr = separated.pop()
            # handle operators that are both unary and binary, minimal BODMAS
            if op in ('+', '-'):
                # simplify/adjust consecutive instances of these operators
                undone = 0
                separated = [s.strip() for s in separated]
                while len(separated) > 1 and not separated[-1]:
                    undone += 1
                    separated.pop()
                if op == '-' and undone % 2 != 0:
                    right_expr = op + right_expr
                elif op == '+':
                    while len(separated) > 1 and set(separated[-1]) <= self.OP_CHARS:
                        right_expr = separated.pop() + right_expr
                    if separated[-1][-1:] in self.OP_CHARS:
                        right_expr = separated.pop() + right_expr
                # hanging op at end of left => unary + (strip) or - (push right)
                separated.append(right_expr)
                dm_ops = ('*', '%', '/', '**')
                dm_chars = set(''.join(dm_ops))

                def yield_terms(s):
                    skip = False
                    for i, term in enumerate(s[:-1]):
                        if skip:
                            skip = False
                            continue
                        if not (dm_chars & set(term)):
                            yield term
                            continue
                        for dm_op in dm_ops:
                            bodmas = list(self._separate(term, dm_op, skip_delims=skip_delim))
                            if len(bodmas) > 1 and not bodmas[-1].strip():
                                bodmas[-1] = (op if op == '-' else '') + s[i + 1]
                                yield dm_op.join(bodmas)
                                skip = True
                                break
                        else:
                            if term:
                                yield term

                    if not skip and s[-1]:
                        yield s[-1]

                separated = list(yield_terms(separated))
                right_expr = separated.pop() if len(separated) > 1 else None
                expr = op.join(separated)
            if right_expr is None:
                continue
            return op, separated, right_expr