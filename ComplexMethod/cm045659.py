def stateful_wrapper(
            packed_state: tuple[api.Value, tuple, int] | None,
            rows: list[tuple[list[api.Value], int]],
        ) -> tuple[api.Value, tuple, int] | None:
            if packed_state is not None:
                serialized_state, _positive_updates_tuple, _cnt = packed_state
                state = reducer_cls.deserialize(serialized_state)
                _positive_updates = list(_positive_updates_tuple)
            else:
                state = None
            positive_updates: list[tuple[api.Value, ...]] = []
            negative_updates = []
            for row, count in rows:
                if count > 0:
                    positive_updates.extend([tuple(row)] * count)
                else:
                    negative_updates.extend([tuple(row)] * (-count))

            if not retract_available and len(negative_updates) > 0:
                if state is not None:
                    assert _positive_updates is not None
                    positive_updates.extend(_positive_updates)
                    _positive_updates = []
                    state = None
                acc = Counter(positive_updates)
                acc.subtract(negative_updates)
                assert all(x >= 0 for x in acc.values())
                positive_updates = list(acc.elements())
                negative_updates = []

            if state is None:
                if neutral_available:
                    state = reducer_cls.neutral()
                    _positive_updates = []
                    _cnt = 0
                elif len(positive_updates) == 0:
                    if len(negative_updates) == 0:
                        return None
                    else:
                        raise ValueError(
                            "Unable to process negative update with this stateful reducer."
                        )
                else:
                    if sort_by_available:
                        positive_updates.sort(
                            key=lambda x: reducer_cls.sort_by(list(x))
                        )
                    state = reducer_cls.from_row(list(positive_updates[0]))
                    if not retract_available:
                        _positive_updates = positive_updates[0:1]
                        _cnt = 0
                    else:
                        _positive_updates = []
                        _cnt = 1
                    positive_updates = positive_updates[1:]

            updates = [(row_up, False) for row_up in positive_updates] + [
                (row_up, True) for row_up in negative_updates
            ]

            if sort_by_available:
                updates.sort(key=lambda x: (reducer_cls.sort_by(list(x[0])), x[1]))
                # insertions first for a given `sort_by` value to be "compatible" with no `sort_by` situation

            for row_up, is_retraction in updates:
                if is_retraction:
                    if not retract_available:
                        raise ValueError(
                            "Unable to process negative update with this stateful reducer."
                        )
                    else:
                        _cnt -= 1
                    val = reducer_cls.from_row(list(row_up))
                    state.retract(val)
                else:
                    if not retract_available:
                        _positive_updates.append(row_up)
                    else:
                        _cnt += 1
                    val = reducer_cls.from_row(list(row_up))
                    state.update(val)

            _positive_updates_tuple = tuple(tuple(x) for x in _positive_updates)
            if retract_available and _cnt == 0:
                # this is fine in this setting, where we process values one by one
                # if this ever becomes accumulated in a tree, we have to handle
                # (A-B) updates, so we have to distinguish `0` from intermediate states
                # accumulating weighted count (weighted by hash) should do fine here
                return None
            return state.serialize(), _positive_updates_tuple, _cnt