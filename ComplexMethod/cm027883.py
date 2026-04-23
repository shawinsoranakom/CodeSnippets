def format_mentions(mentions):
    if not mentions:
        return ""
    mention_texts = []
    for mention in mentions:
        if isinstance(mention, dict):
            text = mention.get("text", "")
            if text and not text.startswith("@"):
                text = f"@{text}"
            mention_texts.append(text)
        elif isinstance(mention, str):
            if not mention.startswith("@"):
                mention = f"@{mention}"
            mention_texts.append(mention)
    return ",".join(mention_texts)