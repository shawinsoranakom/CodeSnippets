def get_existing_attachment(IrAttachment, vals):
    """
    Check if an attachment already exists for the same vals. Return it if
    so, None otherwise.
    """
    fields = dict(vals)
    # Falsy res_id defaults to 0 on attachment creation.
    fields['res_id'] = fields.get('res_id') or 0
    raw, datas = fields.pop('raw', None), fields.pop('datas', None)
    domain = [(field, '=', value) for field, value in fields.items()]
    if fields.get('type') == 'url':
        if 'url' not in fields:
            return None
        domain.append(('checksum', '=', False))
    else:
        if not (raw or datas):
            return None
        domain.append(('checksum', '=', IrAttachment._compute_checksum(raw or b64decode(datas))))
    return IrAttachment.search(domain, limit=1) or None