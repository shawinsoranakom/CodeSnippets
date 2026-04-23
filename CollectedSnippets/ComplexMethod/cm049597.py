def _check_url_to(self):
        for rewrite in self:
            if rewrite.redirect_type in ['301', '302', '308']:
                if not rewrite.url_to:
                    raise ValidationError(_('"URL to" can not be empty.'))
                if not rewrite.url_from:
                    raise ValidationError(_('"URL from" can not be empty.'))
                if rewrite.url_to.startswith('#') or rewrite.url_from.startswith('#'):
                    raise ValidationError(_("URL must not start with '#'."))
                if rewrite.url_to.split('#')[0] == rewrite.url_from.split('#')[0]:
                    raise ValidationError(_("base URL of 'URL to' should not be same as 'URL from'."))

            if rewrite.redirect_type == '308':
                if not rewrite.url_to.startswith('/'):
                    raise ValidationError(_('"URL to" must start with a leading slash.'))
                for param in re.findall('/<.*?>', rewrite.url_from):
                    if param not in rewrite.url_to:
                        raise ValidationError(_('"URL to" must contain parameter %s used in "URL from".', param))
                for param in re.findall('/<.*?>', rewrite.url_to):
                    if param not in rewrite.url_from:
                        raise ValidationError(_('"URL to" cannot contain parameter %s which is not used in "URL from".', param))

                if rewrite.url_to == '/':
                    raise ValidationError(_('"URL to" cannot be set to "/". To change the homepage content, use the "Homepage URL" field in the website settings or the page properties on any custom page.'))

                if any(
                    rule for rule in self.env['ir.http'].routing_map().iter_rules()
                    # Odoo routes are normally always defined without trailing
                    # slashes + strict_slashes=False, but there are exceptions.
                    if rule.rule.rstrip('/') == rewrite.url_to.rstrip('/')
                ):
                    raise ValidationError(_('"URL to" cannot be set to an existing page.'))

                try:
                    converters = self.env['ir.http']._get_converters()
                    routing_map = werkzeug.routing.Map(strict_slashes=False, converters=converters)
                    rule = werkzeug.routing.Rule(rewrite.url_to)
                    routing_map.add(rule)
                except ValueError as e:
                    raise ValidationError(_('"URL to" is invalid: %s', e)) from e