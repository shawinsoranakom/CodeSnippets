def get_lifecycle_rule_from_object(
    lifecycle_conf_rules: LifecycleRules,
    object_key: ObjectKey,
    size: ObjectSize,
    object_tags: dict[str, str],
) -> LifecycleRule:
    for rule in lifecycle_conf_rules:
        if not (expiration := rule.get("Expiration")) or "ExpiredObjectDeleteMarker" in expiration:
            continue

        if not (rule_filter := rule.get("Filter")):
            return rule

        if and_rules := rule_filter.get("And"):
            if all(
                _match_lifecycle_filter(key, value, object_key, size, object_tags)
                for key, value in and_rules.items()
            ):
                return rule

        if any(
            _match_lifecycle_filter(key, value, object_key, size, object_tags)
            for key, value in rule_filter.items()
        ):
            # after validation, we can only one of `Prefix`, `Tag`, `ObjectSizeGreaterThan` or `ObjectSizeLessThan` in
            # the dict. Instead of manually checking, we can iterate of the only key and try to match it
            return rule