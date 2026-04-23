def get_new_page_templates(self, **kw):
        View = request.env['ir.ui.view']
        result = []
        groups_html = View._render_template("website.new_page_template_groups")
        groups_el = etree.fromstring(f'<data>{groups_html}</data>')
        for group_el in groups_el.getchildren():
            group = {
                'id': group_el.attrib['id'],
                'title': group_el.text,
                'templates': [],
            }
            if group_el.attrib['id'] == 'custom':
                for page in request.website._get_website_pages(domain=[('is_new_page_template', '=', True)]):
                    html_tree = html.fromstring(View.with_context(inherit_branding=False)._render_template(
                        page.key,
                    ))
                    wrap_el = html_tree.xpath('//div[@id="wrap"]')[0]
                    group['templates'].append({
                        'key': page.key,
                        'template': html.tostring(wrap_el),
                        'name': page.name,
                    })
                group['is_custom'] = True
                result.append(group)
                continue
            for template in View.search([
                ('mode', '=', 'primary'),
                '|',
                ('key', 'like', escape_psql(f'new_page_template_sections_{group["id"]}_')),
                ('key', 'like', f'configurator_pages_{group["id"]}'),
                request.website.website_domain(),
            ], order='key'):
                try:
                    html_tree = html.fromstring(View.with_context(inherit_branding=False)._render_template(
                        template.key,
                    ))
                    for section_el in html_tree.xpath("//section[@data-snippet]"):
                        # data-snippet must be the short general name
                        snippet = section_el.attrib['data-snippet']
                        # Because the templates are generated from specific
                        # t-snippet-calls such as:
                        # "website.new_page_template_about_0_s_text_block",
                        # the generated data-snippet looks like:
                        # "new_page_template_about_0_s_text_block"
                        # while it should be "s_text_block" only.
                        if '_s_' in snippet:
                            section_el.attrib['data-snippet'] = f's_{snippet.split("_s_")[-1]}'

                    group['templates'].append({
                        'key': template.key,
                        'template': html.tostring(html_tree),
                        'is_from_configurator': 'configurator_pages' in template.key,
                    })
                except Exception as error:
                    if hasattr(error, 'qweb'):
                        # Do not fail if theme is not compatible.
                        logger.warning("Theme not compatible with template %r: %s", template.key, error)
                    else:
                        raise
            if group['templates']:
                result.append(group)
        return result