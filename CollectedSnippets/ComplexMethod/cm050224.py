def _event_exhibitors_get_values(self, event, **searches):
        # init and process search terms
        searches.setdefault('search', '')
        searches.setdefault('countries', '')
        searches.setdefault('sponsorships', '')
        search_domain_base = self._get_event_sponsors_base_domain(event)
        search_domain = search_domain_base

        # search on content
        if searches.get('search'):
            search_domain = Domain.AND([
                search_domain,
                ['|', ('name', 'ilike', searches['search']), ('website_description', 'ilike', searches['search'])]
            ])

        # search on countries
        search_countries = self._get_search_countries(searches['countries'])
        if search_countries:
            search_domain = Domain.AND([
                search_domain,
                [('partner_id.country_id', 'in', search_countries.ids)]
            ])

        # search on sponsor types
        search_sponsorships = self._get_search_sponsorships(searches['sponsorships'])
        if search_sponsorships:
            search_domain = Domain.AND([
                search_domain,
                [('sponsor_type_id', 'in', search_sponsorships.ids)]
            ])

        # fetch data to display; use sudo to allow reading partner info, be sure domain is correct
        event = event.with_context(tz=event.date_tz or 'UTC')
        sorted_sponsors = request.env['event.sponsor'].sudo().search(
            search_domain
        ).sorted(lambda sponsor: (sponsor.sponsor_type_id.sequence, sponsor.sequence))
        sponsors_all = request.env['event.sponsor'].sudo().search(search_domain_base)
        sponsor_types = sponsors_all.mapped('sponsor_type_id')
        sponsor_countries = sponsors_all.mapped('partner_id.country_id').sorted('name')
        # organize sponsors into categories to help display
        sponsor_categories_dict = OrderedDict()
        sponsor_categories = []
        is_event_user = request.env.user.has_group('event.group_event_registration_desk')
        for sponsor in sorted_sponsors:
            if not sponsor_categories_dict.get(sponsor.sponsor_type_id):
                sponsor_categories_dict[sponsor.sponsor_type_id] = request.env['event.sponsor'].sudo()
            sponsor_categories_dict[sponsor.sponsor_type_id] |= sponsor

        for sponsor_category, sponsors in sponsor_categories_dict.items():
            # To display random published sponsors first and random unpublished sponsors last
            if is_event_user:
                published_sponsors = sponsors.filtered(lambda s: s.website_published)
                unpublished_sponsors = sponsors - published_sponsors
                random_sponsors = sample(published_sponsors, len(published_sponsors)) + sample(unpublished_sponsors, len(unpublished_sponsors))
            else:
                random_sponsors = sample(sponsors, len(sponsors))
            sponsor_categories.append({
                'sponsorship': sponsor_category,
                'sponsors': random_sponsors,
            })

        # return rendering values
        return {
            # event information
            'event': event,
            'main_object': event,
            'slots': event.event_slot_ids._filter_open_slots().grouped('date'),
            'sponsor_categories': sponsor_categories,
            'hide_sponsors': True,
            # search information
            'searches': searches,
            'search_count': len(sorted_sponsors),
            'search_key': searches['search'],
            'search_countries': search_countries,
            'search_sponsorships': search_sponsorships,
            'sponsor_types': sponsor_types,
            'sponsor_countries': sponsor_countries,
            # environment
            'hostname': request.httprequest.host.split(':')[0],
            'is_event_user': is_event_user,
        }