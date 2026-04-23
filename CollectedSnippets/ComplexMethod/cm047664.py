def _get_cr(frame):
    # try, in order: cr, cursor, self.env.cr, self.cr,
    # request.env.cr
    if 'cr' in frame.f_locals:
        return frame.f_locals['cr']
    if 'cursor' in frame.f_locals:
        return frame.f_locals['cursor']
    if (local_self := frame.f_locals.get('self')) is not None:
        if (local_env := getattr(local_self, 'env', None)) is not None:
            return local_env.cr
        if (cr := getattr(local_self, 'cr', None)) is not None:
            return cr
    if (req := odoo.http.request) and (env := req.env):
        return env.cr
    return None