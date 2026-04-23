def partners_detail(self, partner_id, **post):
        current_slug = partner_id
        _, partner_id = request.env['ir.http']._unslug(partner_id)
        current_grade, current_country = None, None
        grade_id = post.get('grade_id')
        country_id = post.get('country_id')
        if grade_id:
            current_grade = request.env['res.partner.grade'].browse(int(grade_id)).exists()
        if country_id:
            current_country = request.env['res.country'].browse(int(country_id)).exists()
        if partner_id:
            partner = request.env['res.partner'].sudo().browse(partner_id)
            is_website_restricted_editor = request.env.user.has_group('website.group_website_restricted_editor')
            if partner.exists() and (partner.website_published or is_website_restricted_editor):
                partner_slug = request.env['ir.http']._slug(partner)
                if partner_slug != current_slug:
                    return request.redirect('/partners/%s' % partner_slug)
                values = {
                    'main_object': partner,
                    'partner': partner,
                    'current_grade': current_grade,
                    'current_country': current_country
                }
                return request.render("website_crm_partner_assign.partner", values)
        raise request.not_found()