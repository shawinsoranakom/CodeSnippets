def _verify_condition(condition: list | dict, form: dict, additional_policy_metadata: dict) -> bool:
    if isinstance(condition, dict) and len(condition) > 1:
        raise CommonServiceException(
            code="InvalidPolicyDocument",
            message="Invalid Policy: Invalid Simple-Condition: Simple-Conditions must have exactly one property specified.",
        )

    match condition:
        case {**kwargs}:
            # this is the most performant to check for a dict with only one key
            # alternative version is `key, val = next(iter(dict))`
            for key, val in kwargs.items():
                k = key.lower()
                if k == "bucket":
                    return additional_policy_metadata.get("bucket") == val
                else:
                    return form.get(k) == val

        case ["eq", key, value]:
            k = key.lower()
            if k == "$bucket":
                return additional_policy_metadata.get("bucket") == value

            return k.startswith("$") and form.get(k.lstrip("$")) == value

        case ["starts-with", key, value]:
            # You can set the `starts-with` value to an empty string to accept anything
            return key.startswith("$") and (
                not value or form.get(key.lstrip("$").lower(), "").startswith(value)
            )

        case ["content-length-range", start, end]:
            size = additional_policy_metadata.get("content_length", 0)
            try:
                start, end = int(start), int(end)
            except ValueError:
                return False

            if size < start:
                raise EntityTooSmall(
                    "Your proposed upload is smaller than the minimum allowed size",
                    ProposedSize=size,
                    MinSizeAllowed=start,
                )
            elif size > end:
                raise EntityTooLarge(
                    "Your proposed upload exceeds the maximum allowed size",
                    ProposedSize=size,
                    MaxSizeAllowed=end,
                    HostId=S3_HOST_ID,
                )
            else:
                return True