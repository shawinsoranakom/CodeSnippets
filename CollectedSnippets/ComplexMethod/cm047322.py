def get_attachments(self, extension, ignore_version=False):
        """ Return the ir.attachment records for a given bundle. This method takes care of mitigating
        an issue happening when parallel transactions generate the same bundle: while the file is not
        duplicated on the filestore (as it is stored according to its hash), there are multiple
        ir.attachment records referencing the same version of a bundle. As we don't want to source
        multiple time the same bundle in our `to_html` function, we group our ir.attachment records
        by file name and only return the one with the max id for each group.

        :param extension: file extension (js, min.js, css)
        :param ignore_version: if ignore_version, the url contains a version => web/assets/%/name.extension
                                (the second '%' corresponds to the version),
                               else: the url contains a version equal to that of the self.get_version(type)
                                => web/assets/self.get_version(type)/name.extension.
        """
        unique = ANY_UNIQUE if ignore_version else self.get_version('css' if self.is_css(extension) else 'js')
        url_pattern = self.get_asset_url(
            unique=unique,
            extension=extension,
        )
        query = """
             SELECT max(id)
               FROM ir_attachment
              WHERE create_uid = %s
                AND url like %s
                AND res_model = 'ir.ui.view'
                AND res_id = 0
                AND public = true
           GROUP BY name
           ORDER BY name
        """
        self.env.cr.execute(query, [SUPERUSER_ID, url_pattern])

        attachment_id = [r[0] for r in self.env.cr.fetchall()]
        if not attachment_id and not ignore_version:
            fallback_url_pattern = self.get_asset_url(
                unique=unique,
                extension=extension,
                ignore_params=True,
            )
            self.env.cr.execute(query, [SUPERUSER_ID, fallback_url_pattern])
            similar_attachment_ids = [r[0] for r in self.env.cr.fetchall()]
            if similar_attachment_ids:
                similar = self.env['ir.attachment'].sudo().browse(similar_attachment_ids)
                _logger.info('Found a similar attachment for %s, copying from %s', url_pattern, similar.url)
                url = url_pattern
                values = {
                    'name': similar.name,
                    'mimetype': similar.mimetype,
                    'res_model': 'ir.ui.view',
                    'res_id': False,
                    'type': 'binary',
                    'public': True,
                    'raw': similar.raw,
                    'url': url,
                }
                attachment = self.env['ir.attachment'].with_user(SUPERUSER_ID).create(values)
                attachment_id = attachment.id
                self._clean_attachments(extension, url)

        return self.env['ir.attachment'].sudo().browse(attachment_id)