def process_request(self, request):
        urlconf = getattr(request, "urlconf", settings.ROOT_URLCONF)
        (
            i18n_patterns_used,
            prefixed_default_language,
        ) = is_language_prefix_patterns_used(urlconf)
        language = translation.get_language_from_request(
            request, check_path=i18n_patterns_used
        )
        language_from_path = translation.get_language_from_path(request.path_info)
        if (
            not language_from_path
            and i18n_patterns_used
            and not prefixed_default_language
        ):
            language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()