def search_url_dependencies(self, res_model, res_ids):
        """ Search dependencies just for information. It will not catch 100%
        of dependencies and False positive is more than possible
        Each module could add dependences in this dict

        :returns: a dictionnary where key is the 'categorie' of object related to the given
            view, and the value is the list of text and link to the resource using given page
        """
        dependencies = {}
        current_website = self.get_current_website()
        page_model_name = 'Page'

        def _handle_views_and_pages(views):
            page_views = views.filtered('page_ids')
            views = views - page_views
            if page_views:
                dependencies.setdefault(page_model_name, [])
                dependencies[page_model_name] += [{
                    'field_name': 'Content',
                    'record_name': page.name,
                    'link': page.url,
                    'model_name': page_model_name,
                } for page in page_views.page_ids]
            return views

        # Prepare what's needed to later generate the URL search domain for the
        # given records
        search_criteria = []
        for record in self.env[res_model].browse([int(res_id) for res_id in res_ids]):
            website = 'website_id' in record and record.website_id or current_website
            url = 'website_url' in record and record.website_url or record.url
            search_criteria.append((url, website.website_domain()))

        for model_name, field_name in self._get_html_fields():
            Model = self.env[model_name]
            if not Model.has_access('read'):
                continue

            # Generate the exact domain to search for the URL in this field
            domains = []
            for url, website_domain in search_criteria:
                domains.append(Domain.AND([
                    [(field_name, 'ilike', url)],
                    website_domain if hasattr(Model, 'website_id') else [],
                ]))

            dependency_records = Model.search(Domain.OR(domains))
            if model_name == 'ir.ui.view':
                dependency_records = _handle_views_and_pages(dependency_records)
            if dependency_records:
                model_display_name = self.env['ir.model']._display_name_for([model_name])[0]['display_name']
                field_string = Model.fields_get()[field_name]['string']
                dependencies.setdefault(model_display_name, [])
                dependencies[model_display_name] += [{
                    'field_name': field_string,
                    'record_name': rec.display_name,
                    'link': 'website_url' in rec and rec.website_url or f'/odoo/{model_name}/{rec.id}',
                    'model_name': model_display_name,
                } for rec in dependency_records]

        return dependencies