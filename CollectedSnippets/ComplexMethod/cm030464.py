def set_message_content(msg, message, subtype="rfc822", cte=None,
                       disposition=None, filename=None, cid=None,
                       params=None, headers=None):
    if subtype == 'partial':
        raise ValueError("message/partial is not supported for Message objects")
    if subtype == 'rfc822':
        if cte not in (None, '7bit', '8bit', 'binary'):
            # http://tools.ietf.org/html/rfc2046#section-5.2.1 mandate.
            raise ValueError(
                "message/rfc822 parts do not support cte={}".format(cte))
        # 8bit will get coerced on serialization if policy.cte_type='7bit'.  We
        # may end up claiming 8bit when it isn't needed, but the only negative
        # result of that should be a gateway that needs to coerce to 7bit
        # having to look through the whole embedded message to discover whether
        # or not it actually has to do anything.
        cte = '8bit' if cte is None else cte
    elif subtype == 'external-body':
        if cte not in (None, '7bit'):
            # http://tools.ietf.org/html/rfc2046#section-5.2.3 mandate.
            raise ValueError(
                "message/external-body parts do not support cte={}".format(cte))
        cte = '7bit'
    elif cte is None:
        # http://tools.ietf.org/html/rfc2046#section-5.2.4 says all future
        # subtypes should be restricted to 7bit, so assume that.
        cte = '7bit'
    _prepare_set(msg, 'message', subtype, headers)
    msg.set_payload([message])
    msg['Content-Transfer-Encoding'] = cte
    _finalize_set(msg, disposition, filename, cid, params)