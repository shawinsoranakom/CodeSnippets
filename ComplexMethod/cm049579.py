def update_alt_images(self, imgs):
        if not request.env.user.has_group('website.group_website_restricted_editor'):
            raise werkzeug.exceptions.Forbidden()
        for img in imgs:
            record = request.env[img['res_model']].browse(img['res_id'])
            if not record.has_access('write'):
                continue
            img['field'] = 'arch_db' if img['field'] == 'arch' else img['field']
            tree = html.fromstring(str(record[img['field']]))
            modified = False
            for index, element in enumerate(tree.xpath('//img')):
                imgId = f"{img['res_model']}-{img['res_id']}-{index!s}"
                if imgId == img['id']:
                    if (img['decorative']):
                        element.set('alt', '')
                        element.set('role', 'presentation')
                    else:
                        element.set('alt', markup_escape(img['alt']))
                        element.attrib.pop('role', None)
                    modified = True
            if modified:
                new_html_content = html.tostring(tree, encoding='unicode', method='html')
                record.write({img['field']: new_html_content})