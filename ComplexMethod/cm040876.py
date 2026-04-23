def validate_lifecycle_configuration(lifecycle_conf: BucketLifecycleConfiguration) -> None:
    """
    Validate the Lifecycle configuration following AWS docs
    See https://docs.aws.amazon.com/AmazonS3/latest/userguide/intro-lifecycle-rules.html
    https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutBucketLifecycleConfiguration.html
    :param lifecycle_conf: the bucket lifecycle configuration given by the client
    :raises MalformedXML: when the file doesn't follow the basic structure/required fields
    :raises InvalidArgument: if the `Date` passed for the Expiration is not at Midnight GMT
    :raises InvalidRequest: if there are duplicate tags keys in `Tags` field
    :return: None
    """
    # we only add the `Expiration` header, we don't delete objects yet
    # We don't really expire or transition objects
    # TODO: transition not supported not validated, as we don't use it yet
    if not lifecycle_conf:
        return

    for rule in lifecycle_conf.get("Rules", []):
        if any(req_key not in rule for req_key in ("ID", "Filter", "Status")):
            raise MalformedXML()
        if (non_current_exp := rule.get("NoncurrentVersionExpiration")) is not None:
            if all(
                req_key not in non_current_exp
                for req_key in ("NewerNoncurrentVersions", "NoncurrentDays")
            ):
                raise MalformedXML()

        if rule_filter := rule.get("Filter"):
            if len(rule_filter) > 1:
                raise MalformedXML()

        if (expiration := rule.get("Expiration", {})) and "ExpiredObjectDeleteMarker" in expiration:
            if len(expiration) > 1:
                raise MalformedXML()

        if exp_date := (expiration.get("Date")):
            if exp_date.timetz() != datetime.time(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo("GMT")
            ):
                raise InvalidArgument(
                    "'Date' must be at midnight GMT",
                    ArgumentName="Date",
                    ArgumentValue=exp_date.astimezone(),  # use the locale timezone, that's what AWS does (returns PST?)
                )

        if tags := (rule_filter.get("And", {}).get("Tags")):
            tag_keys = set()
            for tag in tags:
                if (tag_key := tag.get("Key")) in tag_keys:
                    raise InvalidRequest("Duplicate Tag Keys are not allowed.")
                tag_keys.add(tag_key)