def content_assets(self, filename=None, unique=ANY_UNIQUE, nocache=False, assets_params=None):
        env = request.env  # readonly
        assets_params = assets_params or {}
        assert isinstance(assets_params, dict)
        debug_assets = unique == 'debug'
        stream = None
        if unique in ('any', '%'):
            unique = ANY_UNIQUE
        if unique != 'debug':
            url = env['ir.asset']._get_asset_bundle_url(filename, unique, assets_params)
            assert not '%' in url
            domain = [
                ('public', '=', True),
                ('url', '!=', False),
                ('url', '=like', url),
                ('res_model', '=', 'ir.ui.view'),
                ('res_id', '=', 0),
                ('create_uid', '=', SUPERUSER_ID),
            ]
            attachment = env['ir.attachment'].sudo().search(domain, limit=1)
            if attachment:
                stream = env['ir.binary']._get_stream_from(attachment, 'raw', filename)
        if stream is None:
            # try to generate one
            if env.cr.readonly:
                env.cr.rollback()  # reset state to detect newly generated assets
                cursor_manager = env.registry.cursor(readonly=False)
            else:
                # if we don't have a replica, the cursor is not readonly, use the same one to avoid a rollback
                cursor_manager = nullcontext(env.cr)
            with cursor_manager as rw_cr:
                rw_env = api.Environment(rw_cr, env.user.id, {})
                try:
                    if filename.endswith('.map'):
                        _logger.error(".map should have been generated through debug assets, (version %s most likely outdated)", unique)
                        raise request.not_found()
                    bundle_name, rtl, asset_type, autoprefix = rw_env['ir.asset']._parse_bundle_name(filename, debug_assets)
                    css = asset_type == 'css'
                    js = asset_type == 'js'
                    bundle = rw_env['ir.qweb']._get_asset_bundle(
                        bundle_name,
                        css=css,
                        js=js,
                        debug_assets=debug_assets,
                        rtl=rtl,
                        autoprefix=autoprefix,
                        assets_params=assets_params,
                    )
                    # check if the version matches. If not, redirect to the last version
                    if not debug_assets and unique != ANY_UNIQUE and unique != bundle.get_version(asset_type):
                        return request.redirect(bundle.get_link(asset_type))
                    attachment = None
                    if css and bundle.stylesheets:
                        attachment = bundle.css()
                    elif js and bundle.javascripts:
                        attachment = bundle.js()
                    if attachment:
                        stream = rw_env['ir.binary']._get_stream_from(attachment, 'raw', filename)
                except ValueError as e:
                    _logger.warning("Parsing asset bundle %s has failed: %s", filename, e)
                    raise request.not_found() from e
        if stream is None:
            raise request.not_found()
        send_file_kwargs = {'as_attachment': False, 'content_security_policy': None}
        if unique and unique != 'debug':
            send_file_kwargs['immutable'] = True
            send_file_kwargs['max_age'] = http.STATIC_CACHE_LONG
        if nocache:
            send_file_kwargs['max_age'] = None

        return stream.get_response(**send_file_kwargs)