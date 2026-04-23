def run_with_locale(catstr, *locales):
    try:
        import locale
        category = getattr(locale, catstr)
        orig_locale = locale.setlocale(category)
    except AttributeError:
        # if the test author gives us an invalid category string
        raise
    except Exception:
        # cannot retrieve original locale, so do nothing
        locale = orig_locale = None
        if '' not in locales:
            raise unittest.SkipTest('no locales')
    else:
        for loc in locales:
            try:
                locale.setlocale(category, loc)
                break
            except locale.Error:
                pass
        else:
            if '' not in locales:
                raise unittest.SkipTest(f'no locales {locales}')

    try:
        yield
    finally:
        if locale and orig_locale:
            locale.setlocale(category, orig_locale)