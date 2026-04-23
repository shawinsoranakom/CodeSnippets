def get_seo_data(self, res_id, res_model):
        if not request.env.user.has_group('website.group_website_restricted_editor'):
            # Still ok if user can access the record anyway.
            try:
                record = request.env[res_model].browse(res_id)
                record.check_access('write')
            except AccessError:
                raise werkzeug.exceptions.Forbidden()

        fields = ['website_meta_title', 'website_meta_description', 'website_meta_keywords', 'website_meta_og_img']
        res = {'can_edit_seo': True}
        record = request.env[res_model].browse(res_id)
        if res_model == 'website.page':
            fields.extend(['website_indexed', 'website_id'])
            res["website_is_published"] = record.website_published

        try:
            request.website._check_user_can_modify(record)
        except AccessError:
            res['can_edit_seo'] = False
        if request.env.user.has_group('website.group_website_restricted_editor'):
            record = record.sudo()

        res.update(record.read(fields)[0])
        res['has_social_default_image'] = request.website.has_social_default_image

        if res_model not in ('website.page', 'ir.ui.view') and 'seo_name' in record:  # allow custom slugify
            res['seo_name_default'] = request.env['ir.http']._slugify(record.display_name or '')  # default slug, if seo_name become empty
            res['seo_name'] = record.seo_name and request.env['ir.http']._slugify(record.seo_name) or ''

        return res