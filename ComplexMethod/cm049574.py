def sitemap_xml_index(self, **kwargs):
        current_website = request.website
        Attachment = request.env['ir.attachment'].sudo()
        View = request.env['ir.ui.view'].sudo()
        mimetype = 'application/xml;charset=utf-8'
        content = None
        url_root = request.httprequest.url_root
        # For a same website, each domain has its own sitemap (cache)
        hashed_url_root = md5(url_root.encode()).hexdigest()[:8]
        sitemap_base_url = '/sitemap-%d-%s' % (current_website.id, hashed_url_root)

        def create_sitemap(url, content):
            return Attachment.create({
                'raw': content.encode(),
                'mimetype': mimetype,
                'type': 'binary',
                'name': url,
                'url': url,
            })
        dom = [('url', '=', '%s.xml' % sitemap_base_url), ('type', '=', 'binary')]
        sitemap = Attachment.search(dom, limit=1)
        if sitemap:
            # Check if stored version is still valid
            create_date = fields.Datetime.from_string(sitemap.create_date)
            delta = datetime.datetime.now() - create_date
            if delta < SITEMAP_CACHE_TIME:
                content = base64.b64decode(sitemap.datas)

        if not content:
            # Remove all sitemaps in ir.attachments as we're going to regenerated them
            dom = [('type', '=', 'binary'), '|', ('url', '=like', '%s-%%.xml' % sitemap_base_url),
                   ('url', '=', '%s.xml' % sitemap_base_url)]
            sitemaps = Attachment.search(dom)
            sitemaps.unlink()

            pages = 0
            locs = request.website.with_user(request.website.user_id)._enumerate_pages()
            while True:
                values = {
                    'locs': islice(locs, 0, LOC_PER_SITEMAP),
                    'url_root': url_root[:-1],
                }
                urls = View._render_template('website.sitemap_locs', values)
                if urls.strip():
                    content = View._render_template('website.sitemap_xml', {'content': urls})
                    pages += 1
                    last_sitemap = create_sitemap('%s-%d.xml' % (sitemap_base_url, pages), content)
                else:
                    break

            if not pages:
                return request.not_found()
            elif pages == 1:
                # rename the -id-page.xml => -id.xml
                last_sitemap.write({
                    'url': "%s.xml" % sitemap_base_url,
                    'name': "%s.xml" % sitemap_base_url,
                })
            else:
                # TODO: in master/saas-15, move current_website_id in template directly
                pages_with_website = ["%d-%s-%d" % (current_website.id, hashed_url_root, p) for p in range(1, pages + 1)]

                # Sitemaps must be split in several smaller files with a sitemap index
                content = View._render_template('website.sitemap_index_xml', {
                    'pages': pages_with_website,
                    # URLs inside the sitemap index have to be on the same
                    # domain as the sitemap index itself
                    'url_root': url_root,
                })
                create_sitemap('%s.xml' % sitemap_base_url, content)

        return request.make_response(content, [('Content-Type', mimetype)])