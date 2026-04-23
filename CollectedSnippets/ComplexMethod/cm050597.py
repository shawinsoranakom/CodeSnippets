def _search_get_detail(self, website, order, options):
        with_description = options['displayDescription']
        with_date = options['displayDetail']
        my = options.get('my')
        search_tags = options.get('tag')
        slide_category = options.get('slide_category')
        domain = [website.website_domain(), [('is_visible', '=', True)]]
        if my:
            domain.append([('is_member', '=', True)])
        if search_tags:
            ChannelTag = self.env['slide.channel.tag']
            try:
                tag_ids = list(filter(None, [self.env['ir.http']._unslug(tag)[1] for tag in search_tags.split(',')]))
                tags = ChannelTag.search([('id', 'in', tag_ids)]) if tag_ids else ChannelTag
            except Exception:
                tags = ChannelTag
            # Group by group_id
            # OR inside a group, AND between groups.
            for tags_ in tags.grouped('group_id').values():
                domain.append([('tag_ids', 'in', tags_.ids)])
        if slide_category and 'nbr_%s' % slide_category in self:
            domain.append([('nbr_%s' % slide_category, '>', 0)])
        search_fields = ['name']
        fetch_fields = ['name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }
        if with_description:
            search_fields.append('description_short')
            fetch_fields.append('description_short')
            mapping['description'] = {'name': 'description_short', 'type': 'text', 'html': True, 'match': True}
        if with_date:
            fetch_fields.append('slide_last_update')
            mapping['detail'] = {'name': 'slide_last_update', 'type': 'date'}
        return {
            'model': 'slide.channel',
            'base_domain': domain,
            'search_fields': search_fields,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-graduation-cap',
        }