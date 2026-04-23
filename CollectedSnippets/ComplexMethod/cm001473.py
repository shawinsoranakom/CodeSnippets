def build_tags(metadata):
    tags = {}

    ss_tag_frequency = metadata.get("ss_tag_frequency", {})
    if ss_tag_frequency is not None and hasattr(ss_tag_frequency, 'items'):
        for _, tags_dict in ss_tag_frequency.items():
            for tag, tag_count in tags_dict.items():
                tag = tag.strip()
                tags[tag] = tags.get(tag, 0) + int(tag_count)

    if tags and is_non_comma_tagset(tags):
        new_tags = {}

        for text, text_count in tags.items():
            for word in re.findall(re_word, text):
                if len(word) < 3:
                    continue

                new_tags[word] = new_tags.get(word, 0) + text_count

        tags = new_tags

    ordered_tags = sorted(tags.keys(), key=tags.get, reverse=True)

    return [(tag, tags[tag]) for tag in ordered_tags]