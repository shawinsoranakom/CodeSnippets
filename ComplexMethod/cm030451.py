def params(self):
        # The RFC specifically states that the ordering of parameters is not
        # guaranteed and may be reordered by the transport layer.  So we have
        # to assume the RFC 2231 pieces can come in any order.  However, we
        # output them in the order that we first see a given name, which gives
        # us a stable __str__.
        params = {}  # Using order preserving dict from Python 3.7+
        for token in self:
            if not token.token_type.endswith('parameter'):
                continue
            if token[0].token_type != 'attribute':
                continue
            name = token[0].value.strip()
            if name not in params:
                params[name] = []
            params[name].append((token.section_number, token))
        for name, parts in params.items():
            parts = sorted(parts, key=itemgetter(0))
            first_param = parts[0][1]
            charset = first_param.charset
            # Our arbitrary error recovery is to ignore duplicate parameters,
            # to use appearance order if there are duplicate rfc 2231 parts,
            # and to ignore gaps.  This mimics the error recovery of get_param.
            if not first_param.extended and len(parts) > 1:
                if parts[1][0] == 0:
                    parts[1][1].defects.append(errors.InvalidHeaderDefect(
                        'duplicate parameter name; duplicate(s) ignored'))
                    parts = parts[:1]
                # Else assume the *0* was missing...note that this is different
                # from get_param, but we registered a defect for this earlier.
            value_parts = []
            i = 0
            for section_number, param in parts:
                if section_number != i:
                    # We could get fancier here and look for a complete
                    # duplicate extended parameter and ignore the second one
                    # seen.  But we're not doing that.  The old code didn't.
                    if not param.extended:
                        param.defects.append(errors.InvalidHeaderDefect(
                            'duplicate parameter name; duplicate ignored'))
                        continue
                    else:
                        param.defects.append(errors.InvalidHeaderDefect(
                            "inconsistent RFC2231 parameter numbering"))
                i += 1
                value = param.param_value
                if param.extended:
                    try:
                        value = urllib.parse.unquote_to_bytes(value)
                    except UnicodeEncodeError:
                        # source had surrogate escaped bytes.  What we do now
                        # is a bit of an open question.  I'm not sure this is
                        # the best choice, but it is what the old algorithm did
                        value = urllib.parse.unquote(value, encoding='latin-1')
                    else:
                        try:
                            # Explicitly look up the codec for warning generation, see gh-140030
                            # Can be removed in 3.17
                            import codecs
                            codecs.lookup(charset)
                            value = value.decode(charset, 'surrogateescape')
                        except (LookupError, UnicodeEncodeError):
                            # XXX: there should really be a custom defect for
                            # unknown character set to make it easy to find,
                            # because otherwise unknown charset is a silent
                            # failure.
                            value = value.decode('us-ascii', 'surrogateescape')
                        if utils._has_surrogates(value):
                            param.defects.append(errors.UndecodableBytesDefect())
                value_parts.append(value)
            value = ''.join(value_parts)
            yield name, value