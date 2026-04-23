def search_fetch(self, domain, field_names=None, offset=0, limit=None, order=None):
        """ Override to support ordering on my_activity_date_deadline.

        Ordering through web client calls search_read() with an order parameter
        set. Method search_read() then calls search_fetch(). Here we override
        search_fetch() to intercept a search with an order on field
        my_activity_date_deadline. In that case we do the search in two steps.

        First step: fill with deadline-based results

          * Perform a read_group on my activities to get a mapping lead_id / deadline
            Remember date_deadline is required, we always have a value for it. Only
            the earliest deadline per lead is kept.
          * Search leads linked to those activities that also match the asked domain
            and order from the original search request.
          * Results of that search will be at the top of returned results. Use limit
            None because we have to search all leads linked to activities as ordering
            on deadline is done in post processing.
          * Reorder them according to deadline asc or desc depending on original
            search ordering. Finally take only a subset of those leads to fill with
            results matching asked offset / limit.

        Second step: fill with other results. If first step does not gives results
        enough to match offset and limit parameters we fill with a search on other
        leads. We keep the asked domain and ordering while filtering out already
        scanned leads to keep a coherent results.

        All other search and search_read are left untouched by this override to avoid
        side effects. Search_count is not affected by this override.
        """
        if not order or 'my_activity_date_deadline' not in order:
            return super().search_fetch(domain, field_names, offset, limit, order)
        order_items = [order_item.strip().lower() for order_item in (order or self._order).split(',')]
        domain = Domain(domain)

        # Perform a read_group on my activities to get a mapping lead_id / deadline
        # Remember date_deadline is required, we always have a value for it. Only
        # the earliest deadline per lead is kept.
        activity_asc = any('my_activity_date_deadline asc' in item for item in order_items)
        my_lead_activities = self.env['mail.activity']._read_group(
            [('res_model', '=', self._name), ('user_id', '=', self.env.uid)],
            ['res_id'],
            ['date_deadline:min'],
            order='date_deadline:min ASC, res_id',
        )
        my_lead_mapping = dict(my_lead_activities)
        my_lead_ids = list(my_lead_mapping.keys())
        my_lead_domain = Domain('id', 'in', my_lead_ids) & domain
        my_lead_order = ', '.join(item for item in order_items if 'my_activity_date_deadline' not in item)

        # Search leads linked to those activities and order them. See docstring
        # of this method for more details.
        search_res = super().search_fetch(my_lead_domain, field_names, order=my_lead_order)
        my_lead_ids_ordered = sorted(search_res.ids, key=lambda lead_id: my_lead_mapping[lead_id], reverse=not activity_asc)
        # keep only requested window (offset + limit, or offset+)
        my_lead_ids_keep = my_lead_ids_ordered[offset:(offset + limit)] if limit else my_lead_ids_ordered[offset:]
        # keep list of already skipped lead ids to exclude them from future search
        my_lead_ids_skip = my_lead_ids_ordered[:(offset + limit)] if limit else my_lead_ids_ordered

        # do not go further if limit is achieved
        if limit and len(my_lead_ids_keep) >= limit:
            return self.browse(my_lead_ids_keep)

        # Fill with remaining leads. If a limit is given, simply remove count of
        # already fetched. Otherwise keep none. If an offset is set we have to
        # reduce it by already fetch results hereabove. Order is updated to exclude
        # my_activity_date_deadline when calling super() .
        lead_limit = (limit - len(my_lead_ids_keep)) if limit else None
        if offset:
            lead_offset = max((offset - len(search_res), 0))
        else:
            lead_offset = 0
        lead_order = ', '.join(item for item in order_items if 'my_activity_date_deadline' not in item)

        other_lead_res = super().search_fetch(
            Domain('id', 'not in', my_lead_ids_skip) & domain,
            field_names, lead_offset, lead_limit, lead_order,
        )
        return self.browse(my_lead_ids_keep) + other_lead_res