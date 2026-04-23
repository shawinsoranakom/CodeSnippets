def parse(filename):

    with open(filename, encoding='latin1') as f:
        lines = list(f)
    # Remove mojibake in /usr/share/X11/locale/locale.alias.
    # b'\xef\xbf\xbd' == '\ufffd'.encode('utf-8')
    lines = [line for line in lines if '\xef\xbf\xbd' not in line]
    data = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line[:1] == '#':
            continue
        locale, alias = line.split()
        # Fix non-standard locale names, e.g. ks_IN@devanagari.UTF-8
        if '@' in alias:
            alias_lang, _, alias_mod = alias.partition('@')
            if '.' in alias_mod:
                alias_mod, _, alias_enc = alias_mod.partition('.')
                alias = alias_lang + '.' + alias_enc + '@' + alias_mod
        # Strip ':'
        if locale[-1] == ':':
            locale = locale[:-1]
        # Lower-case locale
        locale = locale.lower()
        # Ignore one letter locale mappings (except for 'c')
        if len(locale) == 1 and locale != 'c':
            continue
        if '@' in locale and '@' not in alias:
            # Do not simply remove the "@euro" modifier.
            # Glibc generates separate locales with the "@euro" modifier, and
            # not always generates a locale without it with the same encoding.
            # It can also affect collation.
            if locale.endswith('@euro') and not locale.endswith('.utf-8@euro'):
                alias += '@euro'
        # Normalize encoding, if given
        if '.' in locale:
            lang, encoding = locale.split('.')[:2]
            encoding = encoding.replace('-', '')
            encoding = encoding.replace('_', '')
            locale = lang + '.' + encoding
        data[locale] = alias
    # Conflict with glibc.
    data.pop('el_gr@euro', None)
    data.pop('uz_uz@cyrillic', None)
    data.pop('uz_uz.utf8@cyrillic', None)
    return data