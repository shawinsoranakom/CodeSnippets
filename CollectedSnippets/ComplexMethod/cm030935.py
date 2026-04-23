def split_exception_group(self, eg, types):
        """ Split an EG and do some sanity checks on the result """
        self.assertIsInstance(eg, BaseExceptionGroup)

        match, rest = eg.split(types)
        sg = eg.subgroup(types)

        if match is not None:
            self.assertIsInstance(match, BaseExceptionGroup)
            for e,_ in leaf_generator(match):
                self.assertIsInstance(e, types)

            self.assertIsNotNone(sg)
            self.assertIsInstance(sg, BaseExceptionGroup)
            for e,_ in leaf_generator(sg):
                self.assertIsInstance(e, types)

        if rest is not None:
            self.assertIsInstance(rest, BaseExceptionGroup)

        def leaves(exc):
            return [] if exc is None else [e for e,_ in leaf_generator(exc)]

        # match and subgroup have the same leaves
        self.assertSequenceEqual(leaves(match), leaves(sg))

        match_leaves = leaves(match)
        rest_leaves = leaves(rest)
        # each leaf exception of eg is in exactly one of match and rest
        self.assertEqual(
            len(leaves(eg)),
            len(leaves(match)) + len(leaves(rest)))

        for e in leaves(eg):
            self.assertNotEqual(
                match and e in match_leaves,
                rest and e in rest_leaves)

        # message, cause and context, traceback and note equal to eg
        for part in [match, rest, sg]:
            if part is not None:
                self.assertEqual(eg.message, part.message)
                self.assertIs(eg.__cause__, part.__cause__)
                self.assertIs(eg.__context__, part.__context__)
                self.assertIs(eg.__traceback__, part.__traceback__)
                self.assertEqual(
                    getattr(eg, '__notes__', None),
                    getattr(part, '__notes__', None))

        def tbs_for_leaf(leaf, eg):
            for e, tbs in leaf_generator(eg):
                if e is leaf:
                    return tbs

        def tb_linenos(tbs):
            return [tb.tb_lineno for tb in tbs if tb]

        # full tracebacks match
        for part in [match, rest, sg]:
            for e in leaves(part):
                self.assertSequenceEqual(
                    tb_linenos(tbs_for_leaf(e, eg)),
                    tb_linenos(tbs_for_leaf(e, part)))

        return match, rest