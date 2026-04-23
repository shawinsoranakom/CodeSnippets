def _enumerate_pages(self, query_string=None, force=False):
        """ Available pages in the website/CMS. This is mostly used for links
            generation and can be overridden by modules setting up new HTML
            controllers for dynamic pages (e.g. blog).
            By default, returns template views marked as pages.
            :param str query_string: a (user-provided) string, fetches pages
                                     matching the string
            :returns: a list of mappings with two keys: ``name`` is the displayable
                      name of the resource (page), ``url`` is the absolute URL
                      of the same.
            :rtype: list({name: str, url: str})
        """
        # ==== WEBSITE.PAGES ====
        # '/' already has a http.route & is in the routing_map so it will already have an entry in the xml
        domain = [('view_id', '!=', False), ('url', '!=', '/')]
        if not force:
            domain += [('website_indexed', '=', True), ('visibility', '=', False)]
            # is_visible
            domain += [
                ('website_published', '=', True), ('visibility', '=', False),
                '|', ('date_publish', '=', False), ('date_publish', '<=', fields.Datetime.now())
            ]

        if query_string:
            domain += [('url', 'like', query_string)]

        pages = self._get_website_pages(domain)

        for page in pages:
            record = {'loc': page['url'], 'id': page['id'], 'name': page['name']}
            if page.view_id.priority != 16:
                record['priority'] = min(round(page.view_id.priority / 32.0, 1), 1)
            last_dates = [d for d in (page.write_date, page.view_write_date) if d]
            if last_dates:
                record['lastmod'] = max(last_dates).date()
            yield record

        # ==== CONTROLLERS ====
        router = self.env['ir.http'].routing_map()
        url_set = set()

        sitemap_endpoint_done = set()

        # Helper to normalize URLs while keeping '/' intact
        def _norm(url):
            return '/' if url == '/' else url.rstrip('/')

        # Avoid recomputing identical sitemap callables more than once
        def _unwrap_callable(f):
            # Unwrap functools.partial and bound methods to a stable function key
            if isinstance(f, functools.partial):
                f = f.func
            # Unwrap bound methods (obj.method) to their underlying function
            if isinstance(f, types.MethodType):
                return f.__func__
            return f

        for rule in router.iter_rules():
            sitemap_func = rule.endpoint.routing.get('sitemap')
            if sitemap_func is False:
                continue

            if callable(sitemap_func):
                func_key = _unwrap_callable(sitemap_func)
                if func_key in sitemap_endpoint_done:
                    continue
                sitemap_endpoint_done.add(func_key)
                for loc in sitemap_func(self.with_context(lang=self.default_lang_id.code).env, rule, query_string):
                    loc_norm = {**loc, 'loc': _norm(loc['loc'])}
                    url = loc_norm['loc']
                    if url not in url_set:
                        yield loc_norm
                        url_set.add(url)
                continue

            if not self.rule_is_enumerable(rule):
                continue

            # Warn only if the 'sitemap' key is absent from routing (legacy behavior)
            if 'sitemap' not in rule.endpoint.routing:
                logger.warning('No Sitemap value provided for controller %s (%s)' %
                               (rule.endpoint.original_endpoint, ','.join(rule.endpoint.routing['routes'])))

            converters = rule._converters or {}
            if query_string and not converters and (query_string not in rule.build({}, append_unknown=False)[1]):
                continue

            values = [{}]
            # converters with a domain are processed after the other ones
            convitems = sorted(
                converters.items(),
                key=lambda x: (hasattr(x[1], 'domain') and (x[1].domain != '[]'), rule._trace.index((True, x[0]))))

            for (i, (name, converter)) in enumerate(convitems):
                if 'website_id' in self.env[converter.model]._fields and (not converter.domain or converter.domain == '[]'):
                    converter.domain = "[('website_id', 'in', (False, current_website_id))]"

                newval = []
                for val in values:
                    query = i == len(convitems) - 1 and query_string
                    if query:
                        r = "".join([x[1] for x in rule._trace[1:] if not x[0]])  # remove model converter from route
                        query = sitemap_qs2dom(query, r, self.env[converter.model]._rec_name)
                        if query.is_false():
                            continue

                    for rec in converter.generate(self.env, args=val, dom=query):
                        newval.append(val.copy())
                        newval[-1].update({name: rec.with_context(lang=self.default_lang_id.code)})
                values = newval

            for value in values:
                domain_part, url = rule.build(value, append_unknown=False)
                # Normalize trailing slash but keep '/'
                url = _norm(url)
                pattern = query_string and '*%s*' % "*".join(query_string.split('/'))
                if not query_string or fnmatch.fnmatch(url.lower(), pattern):
                    page = {'loc': url}
                    if url in url_set:
                        continue
                    url_set.add(url)

                    yield page