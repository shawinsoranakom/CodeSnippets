def _(shape: StringShape, graph: ShapeGraph) -> str:
    if shape.enum:
        return shape.enum[0]

    if shape.name in custom_strings:
        return custom_strings[shape.name]

    if (
        shape.name.endswith("ARN")
        or shape.name.endswith("Arn")
        or shape.name.endswith("ArnString")
        or shape.name == "AmazonResourceName"
    ):
        try:
            return generate_arn(shape)
        except re.error:
            LOG.error(
                "Could not generate arn pattern for %s, with pattern %s",
                shape.name,
                shape.metadata.get("pattern", "(no pattern set)"),
            )
            return DEFAULT_ARN

    max_len: int = shape.metadata.get("max") or 256
    min_len: int = shape.metadata.get("min") or 0
    str_len = min(min_len or 6, max_len)

    pattern = shape.metadata.get("pattern")

    if not pattern or pattern in [".*", "^.*$", ".+"]:
        if min_len <= 6 and max_len >= 6:
            # pick a random six-letter word, to spice things up. this will be the case most of the time.
            return random.choice(words)
        else:
            return "a" * str_len
    if shape.name == "EndpointId" and pattern == "^[A-Za-z0-9\\-]+[\\.][A-Za-z0-9\\-]+$":
        # there are sometimes issues with this pattern, because it could create invalid host labels, e.g. b6NOZqj5rIMdcta4IKyKRHvZakH90r.-wzuX6tQ-pB-pTNePY2
        # for simplification we just remove the dash for now
        pattern = "^[A-Za-z0-9]+[\\.][A-Za-z0-9]+$"
    pattern = sanitize_pattern(pattern)

    try:
        # try to return something simple first
        random_string = "a" * str_len
        if re.match(pattern, random_string):
            return random_string

        val = rstr.xeger(pattern)
        # TODO: this will break the pattern if the string needs to end with something that we may cut off.
        return val[: min(max_len, len(val))]
    except re.error:
        # TODO: this will likely break the pattern
        LOG.error(
            "Could not generate pattern for %s, with pattern %s",
            shape.name,
            shape.metadata.get("pattern", "(no pattern set)"),
        )
        return "0" * str_len