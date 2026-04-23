def _normalize_size(x: IRNode, new_size: Sequence[_IntLike]) -> Sequence[_IntLike]:
        """Replace `-1` with correct sizes"""
        sizevars = V.graph.sizevars
        new_size = [sympy.expand(s) for s in new_size]
        old_size = x.get_size()
        old_size = [None] * (len(new_size) - len(old_size)) + list(old_size)
        assert len(new_size) == len(old_size)
        for i in range(len(new_size)):
            if new_size[i] == -1:
                assert old_size[i] is not None
                new_size[i] = old_size[i]
            elif old_size[i] is None or V.graph.sizevars.is_size_one_or_false(
                old_size[i]
            ):
                pass
            elif not has_free_unbacked_symbols(
                old_size
            ) and not has_free_unbacked_symbols(new_size):
                # Sanity check: Expect broadcast compatibility
                #
                # NB: new_size[i] == old_size[i] is expected to already be
                # guarded because the meta formula was expected to have taught
                # us this equality.
                v1 = new_size[i]
                v2 = old_size[i]
                assert v1 is not None
                assert v2 is not None
                diff = v1 - v2
                assert (
                    sizevars.optimization_hint(
                        diff,
                        fallback=0,
                    )
                    == 0
                ), (
                    f"Broadcast failed in ExpandView({x.get_size()}, {new_size}) on dimension {i}"
                )
        return new_size