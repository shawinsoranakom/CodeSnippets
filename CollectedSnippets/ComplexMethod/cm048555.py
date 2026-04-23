def mock_recompute(self, field, ids=None):
            ids_to_compute = self.env.transaction.tocompute.get(field, ())
            ids = ids_to_compute if ids is None else [id_ for id_ in ids if id_ in ids_to_compute]
            if field.store and (
                (self._name == 'account.move' and invoice.id in ids)
                or (self._name == 'account.move.line' and set(invoice.line_ids.ids) & set(ids))
            ):
                fields_recomputed.append(str(field))
            original_recompute[self._name](field, ids)