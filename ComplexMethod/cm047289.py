def _inaccessible_comodel_records(self, model_and_ids: dict[str, Collection[int]], operation: str):
        # check access rights on the records
        if self.env.su:
            return
        for res_model, res_ids in model_and_ids.items():
            res_ids = OrderedSet(filter(None, res_ids))
            if not res_model or not res_ids:
                # nothing to check
                continue
            # forbid access to attachments linked to removed models as we do not
            # know what persmissions should be checked
            if res_model not in self.env:
                for res_id in res_ids:
                    yield res_model, res_id
                continue
            records = self.env[res_model].browse(res_ids)
            if res_model == 'res.users' and len(records) == 1 and self.env.uid == records.id:
                # by default a user cannot write on itself, despite the list of writeable fields
                # e.g. in the case of a user inserting an image into his image signature
                # we need to bypass this check which would needlessly throw us away
                continue
            try:
                records = records._filtered_access(operation)
            except MissingError:
                records = records.exists()._filtered_access(operation)
            res_ids.difference_update(records._ids)
            for res_id in res_ids:
                yield res_model, res_id