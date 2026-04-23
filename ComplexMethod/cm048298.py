def _search_get_detail(self, website, order, options):
        with_description = options['displayDescription']
        with_date = options['displayDetail']
        date = options.get('date', 'all')
        country = options.get('country')
        tags = options.get('tags')
        event_type = options.get('type', 'all')

        domain = [website.website_domain()]
        domain.append([('is_visible_on_website', '=', True)])

        if event_type != 'all':
            domain.append([("event_type_id", "=", int(event_type))])
        search_tags = self.env['event.tag']
        if tags:
            try:
                tag_ids = list(filter(None, [self.env['ir.http']._unslug(tag)[1] for tag in tags.split(',')])) or literal_eval(tags)
            except SyntaxError:
                pass
            else:
                # perform a search to filter on existing / valid tags implicitely + apply rules on color
                search_tags = self.env['event.tag'].search([('id', 'in', tag_ids)])

            # Example: You filter on age: 10-12 and activity: football.
            # Doing it this way allows to only get events who are tagged "age: 10-12" AND "activity: football".
            # Add another tag "age: 12-15" to the search and it would fetch the ones who are tagged:
            # ("age: 10-12" OR "age: 12-15") AND "activity: football
            for tags in search_tags.grouped('category_id').values():
                domain.append([('tag_ids', 'in', tags.ids)])

        no_country_domain = domain.copy()
        if country:
            if country == 'online':
                domain.append([("country_id", "=", False)])
            elif country != 'all':
                domain.append([("country_id", "=", int(country))])

        no_date_domain = domain.copy()
        dates = self._search_build_dates()
        current_date = None
        for date_details in dates:
            if date == date_details[0]:
                domain.append(date_details[2])
                no_country_domain.append(date_details[2])
                if date_details[0] != 'scheduled':
                    current_date = date_details[1]

        search_fields = ['name']
        fetch_fields = ['name', 'website_url', 'address_name']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
            'address_name': {'name': 'address_name', 'type': 'text', 'match': True},
        }
        if with_description:
            search_fields.append('subtitle')
            fetch_fields.append('subtitle')
            mapping['description'] = {'name': 'subtitle', 'type': 'text', 'match': True}
        if with_date:
            mapping['detail'] = {'name': 'range', 'type': 'html'}

        # Bypassing the access rigths of partner to search the address.
        def search_in_address(env, search_term):
            ret = env['event.event'].sudo()._search([
               ('address_search', 'ilike', search_term),
            ])
            return [('id', 'in', ret)]

        return {
            'model': 'event.event',
            'base_domain': domain,
            'search_fields': search_fields,
            'search_extra': search_in_address,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-ticket',
            # for website_event main controller:
            'dates': dates,
            'current_date': current_date,
            'search_tags': search_tags,
            'no_date_domain': no_date_domain,
            'no_country_domain': no_country_domain,
        }