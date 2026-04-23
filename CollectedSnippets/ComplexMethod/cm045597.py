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