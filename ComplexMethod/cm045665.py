def _compute_universe(
        left_table: Table,
        right_table: Table,
        id: clmn.Column | None,
        mode: JoinMode,
    ) -> Universe:
        if id is left_table._id_column:
            if mode == JoinMode.LEFT:
                return left_table._universe
            elif mode == JoinMode.INNER:
                return left_table._universe.subset()
            else:
                raise KeyError("Cannot assign id's for this join type.")
        elif id is right_table._id_column:
            if mode == JoinMode.RIGHT:
                return right_table._universe
            elif mode == JoinMode.INNER:
                return right_table._universe.subset()
            else:
                raise KeyError("Cannot assign id's for this join type.")
        else:
            assert id is None
            ret = Universe()
            if (
                (
                    mode in [JoinMode.LEFT, JoinMode.INNER]
                    and left_table._universe.is_empty()
                )
                or (
                    mode in [JoinMode.RIGHT, JoinMode.INNER]
                    and right_table._universe.is_empty()
                )
                or (
                    mode is JoinMode.OUTER
                    and left_table._universe.is_empty()
                    and right_table._universe.is_empty()
                )
            ):
                ret.register_as_empty(no_warn=False)
            return ret