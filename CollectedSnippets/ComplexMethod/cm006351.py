def validate_icon_atr(cls, v):
        #   const emojiRegex = /\p{Emoji}/u;
        # const isEmoji = emojiRegex.test(data?.node?.icon!);
        # emoji pattern in Python
        if v is None:
            return v
        # we are going to use the emoji library to validate the emoji
        # emojis can be defined using the :emoji_name: syntax

        if not v.startswith(":") and not v.endswith(":"):
            return v
        if not v.startswith(":") or not v.endswith(":"):
            # emoji should have both starting and ending colons
            # so if one of them is missing, we will raise
            msg = f"Invalid emoji. {v} is not a valid emoji."
            raise ValueError(msg)

        emoji_value = emoji.emojize(v, variant="emoji_type")
        if v == emoji_value:
            logger.warning("Invalid emoji. %s is not a valid emoji.", v)
        icon = emoji_value

        if purely_emoji(icon):
            # this is indeed an emoji
            return icon
        # otherwise it should be a valid lucide icon
        if v is not None and not isinstance(v, str):
            msg = "Icon must be a string"
            raise ValueError(msg)
        # is should be lowercase and contain only letters and hyphens
        if v and not v.islower():
            msg = "Icon must be lowercase"
            raise ValueError(msg)
        if v and not v.replace("-", "").isalpha():
            msg = "Icon must contain only letters and hyphens"
            raise ValueError(msg)
        return v