def _add_followers(self, res_model, res_ids, partner_ids, subtypes,
                       check_existing=False, existing_policy='skip'):
        """ Internal method that generates values to insert or update followers. Callers have to
        handle the result, for example by making a valid ORM command, inserting or updating directly
        follower records, ... This method returns two main data

         * first one is a dict which keys are res_ids. Value is a list of dict of values valid for
           creating new followers for the related res_id;
         * second one is a dict which keys are follower ids. Value is a dict of values valid for
           updating the related follower record;

        :param subtypes: optional subtypes for new partner followers. This
          is a dict whose keys are partner IDs and value subtype IDs for that
          partner.
        :param check_existing: if True, check for existing followers for given
          documents and handle them according to existing_policy parameter.
          Setting to False allows to save some computation if caller is sure
          there are no conflict for followers;
        :param existing_policy: if check_existing, tells what to do with already
          existing followers:

          * skip: simply skip existing followers, do not touch them;
          * force: update existing with given subtypes only;
          * replace: replace existing with new subtypes (like force without old / new follower);
          * update: gives an update dict allowing to add missing subtypes (no subtype removal);
        """
        _res_ids = res_ids or [0]
        data_fols, doc_pids = dict(), dict((i, set()) for i in _res_ids)

        if check_existing and res_ids:
            for fid, rid, pid, sids in self._get_subscription_data([(res_model, res_ids)], partner_ids or None):
                if existing_policy != 'force':
                    if pid:
                        doc_pids[rid].add(pid)
                data_fols[fid] = (rid, pid, sids)

            if existing_policy == 'force':
                self.sudo().browse(data_fols.keys()).unlink()

        new, update = dict(), dict()
        for res_id in _res_ids:
            for partner_id in set(partner_ids or []):
                if partner_id not in doc_pids[res_id]:
                    new.setdefault(res_id, list()).append({
                        'res_model': res_model,
                        'partner_id': partner_id,
                        'subtype_ids': [Command.set(subtypes[partner_id])],
                    })
                elif existing_policy in ('replace', 'update'):
                    fol_id, sids = next(((key, val[2]) for key, val in data_fols.items() if val[0] == res_id and val[1] == partner_id), (False, []))
                    new_sids = set(subtypes[partner_id]) - set(sids)
                    old_sids = set(sids) - set(subtypes[partner_id])
                    update_cmd = []
                    if fol_id and new_sids:
                        update_cmd += [Command.link(sid) for sid in new_sids]
                    if fol_id and old_sids and existing_policy == 'replace':
                        update_cmd += [Command.unlink(sid) for sid in old_sids]
                    if update_cmd:
                        update[fol_id] = {'subtype_ids': update_cmd}

        return new, update