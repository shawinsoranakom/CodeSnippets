def _open_groups(
        self,
        *,
        records_opening_info: list[dict[str, Any]],
        groups: list[dict],
        domain: Domain,
        groupby: list[str],
        aggregates: list[str],
        dict_order: dict[str, str],
        auto_unfold: bool,
        opening_info: list[dict] | None,
        unfold_read_default_limit: int | None,
        parent_opening_info: list[dict] | None,
        parent_group_domain: Domain,
    ):
        max_number_opened_group = self.env.context.get('max_number_opened_groups') or MAX_NUMBER_OPENED_GROUPS

        parent_opening_info_dict = {
            info_opening['value']: info_opening
            for info_opening in parent_opening_info or ()
        }
        groupby_spec = groupby[0]
        field = self._fields[groupby_spec.split(':')[0].split('.')[0]]
        nb_opened_group = 0

        last_level = len(groupby) == 1
        if not last_level:
            read_group_order = self._get_read_group_order(dict_order, [groupby[1]], aggregates)

        for group in groups:
            # Remove __fold information, no need for the webclient,
            # the groups is unfold if __groups/__records exists
            fold_info = '__fold' in group
            fold = group.pop('__fold', False)

            groupby_value = group[groupby_spec]
            # For relational/date/datetime/property tags field
            raw_groupby_value = groupby_value[0] if isinstance(groupby_value, tuple) else groupby_value

            limit = unfold_read_default_limit
            offset = 0
            progressbar_domain = subgroup_opening_info = None
            if opening_info and raw_groupby_value in parent_opening_info_dict:
                group_info = parent_opening_info_dict[raw_groupby_value]
                if group_info['folded']:
                    continue
                limit = group_info['limit']
                offset = group_info['offset']
                progressbar_domain = group_info.get('progressbar_domain')
                subgroup_opening_info = group_info.get('groups')

            elif (
                # Auto Fold/unfold
                (not auto_unfold and not fold_info)
                or nb_opened_group >= max_number_opened_group
                or fold
                # Empty recordset is folded by default
                or (field.relational and not group[groupby_spec])
            ):
                continue

            # => Open group
            nb_opened_group += 1
            if last_level:  # Open records
                records_domain = parent_group_domain & Domain(group['__extra_domain'])

                # when we click on a part of the progress bar, we force a domain
                # for a specific open column/group, we want to keep this for the next reload
                if progressbar_domain:
                    records_domain &= Domain(progressbar_domain)

                # TODO also for groups ?
                # Simulate the same behavior than in relational_model.js
                # If the offset is bigger than the number of record (a record has been deleted)
                # reset the offset to 0 and add the information to the group to update the webclient too
                if offset and offset >= group['__count']:
                    group['__offset'] = offset = 0

                records_opening_info.append({
                    'domain': records_domain,
                    'limit': limit,
                    'offset': offset,
                    'group': group,
                })

            else:  # Open subgroups

                subgroup_domain = parent_group_domain
                if group['__extra_domain']:
                    subgroup_domain &= Domain(group['__extra_domain'])
                # That's not optimal but hard to batch because of limit/offset.
                # Moreover it isn't critical since it is when user opens group manually, then
                # the number of it should be small.
                subgroups, length = self._formatted_read_group_with_length(
                    domain=(subgroup_domain & domain),
                    groupby=[groupby[1]], aggregates=aggregates,
                    offset=offset, limit=limit, order=read_group_order)

                group['__groups'] = {
                    'groups': subgroups,
                    'length': length,
                }
                self._open_groups(
                    records_opening_info=records_opening_info,
                    groups=subgroups,
                    domain=domain,
                    groupby=groupby[1:],
                    aggregates=aggregates,
                    dict_order=dict_order,
                    auto_unfold=False,
                    opening_info=opening_info,
                    unfold_read_default_limit=unfold_read_default_limit,
                    parent_opening_info=subgroup_opening_info,
                    parent_group_domain=subgroup_domain,
                )