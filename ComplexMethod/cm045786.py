def remove_emails_from_data(payload):
    if isinstance(payload, str):
        # The string case is obvious: it's getting split and then merged back after
        # the email-like substrings are removed
        return " ".join([item for item in payload.split(" ") if "@" not in item])

    if isinstance(payload, list):
        # If the payload is a list, one needs to remove emails from each of its
        # elements and then return the result of the processing
        result = []
        for item in payload:
            result.append(remove_emails_from_data(item))
        return result

    if isinstance(payload, dict):
        # If the payload is a dict, one needs to remove emails from its keys and
        # values and then return the clean dict
        result = {}
        for key, value in payload.items():
            # There are no e-mails in the keys of the returned dict
            # So, we only need to remove them from values
            value = remove_emails_from_data(value)
            result[key] = value
        return result

    # If the payload is neither str nor list or dict, it's a primitive type:
    # namely, a boolean, a float, or an int. It can also be just null.
    #
    # But in any case, there is no data to remove from such an element.
    return payload