def setUpModule():
    global candidate_locales
    # Issue #13441: Skip some locales (e.g. cs_CZ and hu_HU) on Solaris to
    # workaround a mbstowcs() bug. For example, on Solaris, the hu_HU locale uses
    # the locale encoding ISO-8859-2, the thousands separator is b'\xA0' and it is
    # decoded as U+30000020 (an invalid character) by mbstowcs().
    if sys.platform == 'sunos5':
        old_locale = locale.setlocale(locale.LC_ALL)
        try:
            locales = []
            for loc in candidate_locales:
                try:
                    locale.setlocale(locale.LC_ALL, loc)
                except Error:
                    continue
                encoding = locale.getencoding()
                try:
                    localeconv()
                except Exception as err:
                    print("WARNING: Skip locale %s (encoding %s): [%s] %s"
                        % (loc, encoding, type(err), err))
                else:
                    locales.append(loc)
            candidate_locales = locales
        finally:
            locale.setlocale(locale.LC_ALL, old_locale)

    # Workaround for MSVC6(debug) crash bug
    if "MSC v.1200" in sys.version:
        def accept(loc):
            a = loc.split(".")
            return not(len(a) == 2 and len(a[-1]) >= 9)
        candidate_locales = [loc for loc in candidate_locales if accept(loc)]