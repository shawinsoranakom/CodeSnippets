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