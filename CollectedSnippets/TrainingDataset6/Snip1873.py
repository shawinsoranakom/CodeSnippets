def _add_lang_code_to_url(url: str, lang_code: str) -> str:
    if url.startswith(TIANGOLO_COM):
        rel_url = url[len(TIANGOLO_COM) :]
        if not rel_url.startswith(ASSETS_URL_PREFIXES):
            url = url.replace(TIANGOLO_COM, f"{TIANGOLO_COM}/{lang_code}")
    return url