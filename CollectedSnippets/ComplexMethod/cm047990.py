def save_unsplash_url(self, unsplashurls=None, **kwargs):
        """
            unsplashurls = {
                image_id1: {
                    url: image_url,
                    download_url: download_url,
                },
                image_id2: {
                    url: image_url,
                    download_url: download_url,
                },
                .....
            }
        """
        def slugify(s):
            ''' Keeps only alphanumeric characters, hyphens and spaces from a string.
                The string will also be truncated to 1024 characters max.
                :param s: the string to be filtered
                :return: the sanitized string
            '''
            return "".join([c for c in s if c.isalnum() or c in list("- ")])[:1024]

        if not unsplashurls:
            return []

        uploads = []

        query = kwargs.get('query', '')
        query = slugify(query)

        res_model = kwargs.get('res_model', 'ir.ui.view')
        if res_model != 'ir.ui.view' and kwargs.get('res_id'):
            res_id = int(kwargs['res_id'])
        else:
            res_id = None

        for key, value in unsplashurls.items():
            url = value.get('url')
            try:
                if not url.startswith(('https://images.unsplash.com/', 'https://plus.unsplash.com/')) and not modules.module.current_test:
                    logger.exception("ERROR: Unknown Unsplash URL!: " + url)
                    raise Exception(_("ERROR: Unknown Unsplash URL!"))

                req = requests.get(url)
                if req.status_code != requests.codes.ok:
                    continue

                # get mime-type of image url because unsplash url dosn't contains mime-types in url
                image = req.content
            except requests.exceptions.ConnectionError as e:
                logger.exception("Connection Error: " + str(e))
                continue
            except requests.exceptions.Timeout as e:
                logger.exception("Timeout: " + str(e))
                continue

            image = image_process(image, verify_resolution=True)
            mimetype = guess_mimetype(image)
            # append image extension in name
            query += mimetypes.guess_extension(mimetype) or ''

            # /unsplash/5gR788gfd/lion
            url_frags = ['unsplash', key, query]

            attachment_data = {
                'name': '_'.join(url_frags),
                'url': '/' + '/'.join(url_frags),
                'data': image,
                'res_id': res_id,
                'res_model': res_model,
            }
            attachment = HTML_Editor._attachment_create(self, **attachment_data)
            if value.get('description'):
                attachment.description = value.get('description')
            attachment.generate_access_token()
            uploads.append(attachment._get_media_info())

            # Notifies Unsplash from an image download. (API requirement)
            self._notify_download(value.get('download_url'))

        return uploads