def i18n(request):
    from django.utils import translation

    return {
        "LANGUAGES": settings.LANGUAGES,
        "LANGUAGE_CODE": translation.get_language(),
        "LANGUAGE_BIDI": translation.get_language_bidi(),
    }