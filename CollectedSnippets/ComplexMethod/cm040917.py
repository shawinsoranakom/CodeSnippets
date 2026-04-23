def _matching_filter(
    notification_filter: NotificationConfigurationFilter | None, key_name: str
) -> bool:
    """
    See: https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-filtering.html
    S3 allows filtering notification events with rules about the key name.
    If the key does not have a filter rule, or if it matches the rule, then returns that the event should be sent
    :param notification_filter: the Filter structure from NotificationConfiguration
    :param key_name: the key name of the key concerned by the event
    :return: boolean indicating if the key name matches the rules and the event should be sent
    """
    # TODO: implement wildcard filtering
    if not notification_filter or not notification_filter.get("Key", {}).get("FilterRules"):
        return True
    filter_rules = notification_filter.get("Key").get("FilterRules")
    for rule in filter_rules:
        name = rule.get("Name", "").lower()
        value = rule.get("Value", "")
        if name == "prefix" and not key_name.startswith(value):
            return False
        elif name == "suffix" and not key_name.endswith(value):
            return False

    return True