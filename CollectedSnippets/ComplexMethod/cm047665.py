def _get_lang(frame, default_lang='') -> str:
    # get from: context.get('lang'), kwargs['context'].get('lang'),
    if local_context := frame.f_locals.get('context'):
        if lang := local_context.get('lang'):
            return lang
    if (local_kwargs := frame.f_locals.get('kwargs')) and (local_context := local_kwargs.get('context')):
        if lang := local_context.get('lang'):
            return lang
    # get from self.env
    log_level = logging.WARNING
    local_self = frame.f_locals.get('self')
    local_env = local_self is not None and getattr(local_self, 'env', None)
    if local_env:
        if lang := local_env.lang:
            return lang
        # we found the env, in case we fail, just log in debug
        log_level = logging.DEBUG
    # get from request?
    if (req := odoo.http.request) and (env := req.env) and (lang := env.lang):
        return lang
    # Last resort: attempt to guess the language of the user
    # Pitfall: some operations are performed in sudo mode, and we
    #          don't know the original uid, so the language may
    #          be wrong when the admin language differs.
    cr = _get_cr(frame)
    uid = _get_uid(frame)
    if cr and uid:
        from odoo import api  # noqa: PLC0415
        env = api.Environment(cr, uid, {})
        if lang := env['res.users'].context_get().get('lang'):
            return lang
    # fallback
    if default_lang:
        _logger.debug('no translation language detected, fallback to %s', default_lang)
        return default_lang
    # give up
    _logger.log(log_level, 'no translation language detected, skipping translation %s', frame, stack_info=True)
    return ''