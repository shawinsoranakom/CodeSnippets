def test_no_new_methods_was_added_to_api():
    def is_public(name: str) -> bool:
        return not name.startswith("_")

    dict_public_names = {name for name in dir({}) if is_public(name)}
    hash_public_names = {name for name in dir(HashMap()) if is_public(name)}

    assert dict_public_names > hash_public_names
