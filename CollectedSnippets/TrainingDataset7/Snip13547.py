def language_name_translated(lang_code):
    english_name = translation.get_language_info(lang_code)["name"]
    return translation.gettext(english_name)