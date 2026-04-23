def _refresh(self):
        _logger.debug("Refreshing website.route")
        ir_http = self.env['ir.http']
        tocreate = []
        paths = {rec.path: rec for rec in self.search([])}
        for url, endpoint in ir_http._generate_routing_rules(self.pool._init_modules, converters=ir_http._get_converters()):
            if 'GET' in (endpoint.routing.get('methods') or ['GET']):
                if paths.get(url):
                    paths.pop(url)
                else:
                    tocreate.append({'path': url})

        if tocreate:
            _logger.info("Add %d website.route" % len(tocreate))
            self.create(tocreate)

        if paths:
            find = self.search([('path', 'in', list(paths.keys()))])
            _logger.info("Delete %d website.route" % len(find))
            find.unlink()