def is_valid_locale(locale):
    return re.match(r"^[a-z]+$", locale) or re.match(r"^[a-z]+_[A-Z0-9].*$", locale)