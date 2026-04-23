def validate_tag_set(
    tag_set: TagSet, type_set: Literal["bucket", "object", "create-bucket"] = "bucket"
):
    keys = set()
    for tag in tag_set:
        if set(tag) != {"Key", "Value"}:
            raise MalformedXML()

        key = tag["Key"]
        value = tag["Value"]

        if key is None or value is None:
            raise MalformedXML()

        if key in keys:
            raise InvalidTag(
                "Cannot provide multiple Tags with the same key",
                TagKey=key,
            )

        if key.startswith("aws:"):
            if type_set == "bucket":
                message = "System tags cannot be added/updated by requester"
            elif type_set == "object":
                message = "Your TagKey cannot be prefixed with aws:"
            else:
                message = 'User-defined tag keys can\'t start with "aws:". This prefix is reserved for system tags. Remove "aws:" from your tag keys and try again.'
            raise InvalidTag(
                message,
                # weirdly, AWS does not return the `TagKey` field here, but it does if the TagKey does not match the
                # regex in the next step
                TagKey=key if type_set != "create-bucket" else None,
            )

        if not TAG_REGEX.match(key):
            raise InvalidTag(
                "The TagKey you have provided is invalid",
                TagKey=key,
            )
        elif not TAG_REGEX.match(value):
            raise InvalidTag(
                "The TagValue you have provided is invalid", TagKey=key, TagValue=value
            )

        keys.add(key)