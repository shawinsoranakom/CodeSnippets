def _merge(self) -> pw.Table:
        right_first = (
            self._direction == Direction.BACKWARD and self._mode == pw.JoinMode.LEFT
        ) or (self._direction == Direction.FORWARD and self._mode == pw.JoinMode.RIGHT)
        orig_data = {
            k: data.table.select(
                side=data.side,
                instance=data.make_instance(),
                orig_id=data.table.id,
                key=data.make_sort_key(right_first),
                t=data.t,
                **{
                    req_col.internal_name: (
                        req_col.column if data.side == req_col.side else req_col.default
                    )
                    for req_col in self._all_cols
                },
            )
            for k, data in self._side_data.items()
        }
        target = pw.Table.concat_reindex(*orig_data.values())

        target += target.sort(key=pw.this.key, instance=pw.this.instance)

        next_table = _build_groups(target, dir_next=True)
        prev_table = _build_groups(target, dir_next=False)
        m = target + target.select(
            next_same=next_table.peer_same,
            next_diff=next_table.peer_diff,
            prev_same=prev_table.peer_same,
            prev_diff=prev_table.peer_diff,
        )
        peer_elem = None
        if self._direction == Direction.BACKWARD:
            peer_elem = m.prev_diff
        elif self._direction == Direction.FORWARD:
            peer_elem = m.next_diff
        elif self._direction == Direction.NEAREST:

            def select_nearest(
                cur_t: expr.ColumnReference,
                prev_id: expr.ColumnReference,
                next_id: expr.ColumnReference,
                prev_t: expr.ColumnReference,
                next_t: expr.ColumnReference,
            ):
                return pw.if_else(
                    prev_id.is_none(),
                    next_id,
                    pw.if_else(
                        next_id.is_none(),
                        prev_id,
                        pw.if_else(
                            cur_t - pw.unwrap(prev_t) < pw.unwrap(next_t) - cur_t,
                            prev_id,
                            next_id,
                        ),
                    ),
                )

            peer_elem = select_nearest(
                m.t,
                m.prev_diff,
                m.next_diff,
                m.ix(m.prev_diff, optional=True).t,
                m.ix(m.next_diff, optional=True).t,
            )

        else:
            raise ValueError(f"Unsupported direction: {self._direction}")
        m += m.select(peer_elem=peer_elem)

        def fill_self(m_self: pw.Table, side: bool):
            return {
                req.output_name: m_self[req.internal_name]
                for req in self._all_cols
                if req.side == side
            }

        def fill_peer(m_self: pw.Table, side: bool):
            reqs = [req for req in self._all_cols if req.side != side]

            reqs_with_default = [req for req in reqs if req.default is not None]
            reqs_wo_default = [req for req in reqs if req.default is None]
            m_with_peer = m_self.filter(m_self.peer_elem.is_not_none())

            res_default = m_self.select(
                **{req.output_name: req.default for req in reqs_with_default}
            )
            res_default <<= m_with_peer.select(
                **{
                    req.output_name: m.ix(m_with_peer.peer_elem)[req.internal_name]
                    for req in reqs_with_default
                }
            )

            res = {
                req.output_name: m.ix(m_self.peer_elem, optional=True)[
                    req.internal_name
                ]
                for req in reqs_wo_default
            }
            res.update(dict(res_default))
            return res

        if self._mode in [pw.JoinMode.LEFT, pw.JoinMode.OUTER]:
            m0 = m.filter(~m.side)
            m0 = m0.update_types(**orig_data[False].typehints())

        if self._mode in [pw.JoinMode.RIGHT, pw.JoinMode.OUTER]:
            m1 = m.filter(m.side)
            m1 = m1.update_types(**orig_data[True].typehints())

        if self._mode == pw.JoinMode.LEFT:
            res = m0.select(
                pw.this.instance,
                pw.this.t,
                pw.this.key,
                pw.this.side,
                **{sel_col.output_name: sel_col.default for sel_col in self._all_cols},
            )
            res = res.with_columns(**fill_self(m0, False), **fill_peer(m0, False))

        if self._mode == pw.JoinMode.RIGHT:
            res = m1.select(
                pw.this.instance,
                pw.this.t,
                pw.this.key,
                pw.this.side,
                **{sel_col.output_name: sel_col.default for sel_col in self._all_cols},
            )
            res = res.with_columns(**fill_self(m1, True), **fill_peer(m1, True))

        if self._mode == pw.JoinMode.OUTER:
            res = m.select(
                m.instance,
                m.t,
                m.key,
                m.side,
                **{sel_col.output_name: sel_col.default for sel_col in self._all_cols},
            )
            res <<= m0.select(**fill_self(m0, False), **fill_peer(m0, False))
            res <<= m1.select(**fill_self(m1, True), **fill_peer(m1, True))

        return res