def save_attachment(self, extension, content):
        """Record the given bundle in an ir.attachment and delete
        all other ir.attachments referring to this bundle (with the same name and extension).

        :param extension: extension of the bundle to be recorded
        :param content: bundle content to be recorded

        :return the ir.attachment records for a given bundle.
        """
        assert extension in ('js', 'min.js', 'js.map', 'css', 'min.css', 'css.map', 'xml', 'min.xml')
        ira = self.env['ir.attachment']

        # Set user direction in name to store two bundles
        # 1 for ltr and 1 for rtl, this will help during cleaning of assets bundle
        # and allow to only clear the current direction bundle
        # (this applies to css bundles only)
        fname = '%s.%s' % (self.name, extension)
        mimetype = (
            'text/css' if extension in ['css', 'min.css'] else
            'text/xml' if extension in ['xml', 'min.xml'] else
            'application/json' if extension in ['js.map', 'css.map'] else
            'application/javascript'
        )
        unique = self.get_version('css' if self.is_css(extension) else 'js')
        url = self.get_asset_url(
            unique=unique,
            extension=extension,
        )
        values = {
            'name': fname,
            'mimetype': mimetype,
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'raw': content.encode('utf8'),
            'url': url,
        }
        attachment = ira.with_user(SUPERUSER_ID).create(values)

        _logger.info('Generating a new asset bundle attachment %s (id:%s)', attachment.url, attachment.id)

        self._clean_attachments(extension, url)

        # For end-user assets (common and backend), send a message on the bus
        # to invite the user to refresh their browser
        if self.env and 'bus.bus' in self.env and self.name in self.TRACKED_BUNDLES:
            self.env['bus.bus']._sendone('broadcast', 'bundle_changed', {
                'server_version': release.version # Needs to be dynamically imported
            })
            _logger.debug('Asset Changed: bundle: %s -- version: %s', self.name, unique)

        return attachment