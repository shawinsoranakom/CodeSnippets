def _compute_image_src(self):
        for attachment in self:
            # Only add a src for supported images
            if not attachment.mimetype or attachment.mimetype.split(';')[0] not in SUPPORTED_IMAGE_MIMETYPES:
                attachment.image_src = False
                continue

            if attachment.type == 'url':
                if attachment.url.startswith('/'):
                    # Local URL
                    attachment.image_src = attachment.url
                else:
                    name = quote(attachment.name)
                    attachment.image_src = '/web/image/%s-redirect/%s' % (attachment.id, name)
            else:
                # Adding unique in URLs for cache-control
                unique = attachment.checksum[:8]
                if attachment.url:
                    # For attachments-by-url, unique is used as a cachebuster. They
                    # currently do not leverage max-age headers.
                    separator = '&' if '?' in attachment.url else '?'
                    attachment.image_src = '%s%sunique=%s' % (attachment.url, separator, unique)
                else:
                    name = quote(attachment.name)
                    attachment.image_src = '/web/image/%s-%s/%s' % (attachment.id, unique, name)