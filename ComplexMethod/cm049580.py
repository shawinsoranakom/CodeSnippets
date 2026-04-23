def update_broken_links(self, links):
        if not request.env.user.has_group('website.group_website_restricted_editor'):
            raise werkzeug.exceptions.Forbidden()
        for link in links:
            record = request.env[link['res_model']].browse(link['res_id'])
            if not record.has_access('write'):
                continue
            link['field'] = 'arch_db' if link['field'] == 'arch' else link['field']
            tree = html.fromstring(str(record[link['field']]))
            modified = False
            for element in tree.xpath('//a'):
                href = element.get('href')
                if href and (link['oldLink'] == href or link['oldLink'] == href + '/'):
                    if link['remove']:
                        element.drop_tag()
                    else:
                        element.set('href', markup_escape(link['newLink']))
                    modified = True
            if modified:
                new_html_content = html.tostring(tree, encoding='unicode', method='html')
                record.write({link['field']: new_html_content})