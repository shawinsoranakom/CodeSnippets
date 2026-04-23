def _pre_dispatch(cls, rule, args):
        ICP = request.env['ir.config_parameter'].with_user(SUPERUSER_ID)

        # Change the default database-wide 128MiB upload limit on the
        # ICP value. Do it before calling http's generic pre_dispatch
        # so that the per-route limit @route(..., max_content_length=x)
        # takes over.
        try:
            key = 'web.max_file_upload_size'
            if (value := ICP.get_param(key, None)) is not None:
                request.httprequest.max_content_length = int(value)
        except ValueError:  # better not crash on ALL requests
            _logger.error("invalid %s: %r, using %s instead",
                key, value, request.httprequest.max_content_length,
            )

        request.dispatcher.pre_dispatch(rule, args)

        # verify the default language set in the context is valid,
        # otherwise fallback on the company lang, english or the first
        # lang installed
        env = request.env if request.env.uid else request.env['base'].with_user(SUPERUSER_ID).env
        request.update_context(lang=get_lang(env).code)

        # Replace uid and lang placeholder by the current request.env.uid and request.env.lang
        # before checking the access.
        for key, val in list(args.items()):
            if not isinstance(val, models.BaseModel):
                continue

            args[key] = val.with_env(request.env)

        for key, val in list(args.items()):
            if not isinstance(val, models.BaseModel):
                continue

            try:
                # explicitly crash now, instead of crashing later
                args[key].check_access('read')
            except (odoo.exceptions.AccessError, odoo.exceptions.MissingError) as e:
                # custom behavior in case a record is not accessible / has been removed
                if handle_error := rule.endpoint.routing.get('handle_params_access_error'):
                    if response := handle_error(e, **args):
                        werkzeug.exceptions.abort(response)
                if request.env.user.is_public or isinstance(e, odoo.exceptions.MissingError):
                    raise werkzeug.exceptions.NotFound() from e
                raise