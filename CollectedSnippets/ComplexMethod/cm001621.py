def get_closet_checkpoint_match(search_string):
    if not search_string:
        return None

    checkpoint_info = checkpoint_aliases.get(search_string, None)
    if checkpoint_info is not None:
        return checkpoint_info

    found = sorted([info for info in checkpoints_list.values() if search_string in info.title], key=lambda x: len(x.title))
    if found:
        return found[0]

    search_string_without_checksum = re.sub(re_strip_checksum, '', search_string)
    found = sorted([info for info in checkpoints_list.values() if search_string_without_checksum in info.title], key=lambda x: len(x.title))
    if found:
        return found[0]

    return None