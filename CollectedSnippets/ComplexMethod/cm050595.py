def _get_categorized_slides(self, base_domain, order, force_void=True, limit=False, offset=False):
        """ Return an ordered structure of slides by categories within a given
        base_domain that must fulfill slides. As a course structure is based on
        its slides sequences, uncategorized slides must have the lowest sequences.

        Example
          * category 1 (sequence 1), category 2 (sequence 3)
          * slide 1 (sequence 0), slide 2 (sequence 2)
          * course structure is: slide 1, category 1, slide 2, category 2
            * slide 1 is uncategorized,
            * category 1 has one slide : Slide 2
            * category 2 is empty.

        Backend and frontend ordering is the same, uncategorized first. It
        eases resequencing based on DOM / displayed order, notably when
        drag n drop is involved. """
        self.ensure_one()
        all_categories = self.env['slide.slide'].sudo().search([('channel_id', '=', self.id), ('is_category', '=', True)])
        all_slides = self.env['slide.slide'].sudo().search(base_domain, order=order)
        category_data = []

        # Prepare all categories by natural order
        for category in all_categories:
            category_slides = all_slides.filtered(lambda slide: slide.category_id == category)
            if not category_slides and not force_void:
                continue
            category_data.append({
                'category': category, 'id': category.id,
                'name': category.name, 'slug_name': self.env['ir.http']._slug(category),
                'total_slides': len(category_slides),
                'slides': category_slides[(offset or 0):(limit + offset or len(category_slides))],
            })

        # Add uncategorized slides in first position
        uncategorized_slides = all_slides.filtered(lambda slide: not slide.category_id)
        if uncategorized_slides or force_void:
            category_data.insert(0, {
                'category': False, 'id': False,
                'name': _('Uncategorized'), 'slug_name': _('Uncategorized'),
                'total_slides': len(uncategorized_slides),
                'slides': uncategorized_slides[(offset or 0):(offset + limit or len(uncategorized_slides))],
            })

        return category_data