def score(properties: DeviceProperties, other: DeviceProperties) -> float:
        """
        Returns score indicating how similar two instances of the `Properties` tuple are.
        Rules are as follows:
            * Matching `type` adds one point, semi-matching `type` adds 0.1 point (e.g. cuda and rocm).
            * If types match, matching `major` adds another point, and then matching `minor` adds another.
            * The Default expectation (None, None) is worth 0.5 point, which is better than semi-matching. More on this
            in the `is_default` function.
        """
        device_type, major, minor = properties
        other_device_type, other_major, other_minor = other

        score = 0
        # Matching device type, maybe major and minor
        if device_type is not None and device_type == other_device_type:
            score += 1
            if major is not None and major == other_major:
                score += 1
                if minor is not None and minor == other_minor:
                    score += 1
        # Semi-matching device type, which carries less importance than the default expectation
        elif device_type in ["cuda", "rocm"] and other_device_type in ["cuda", "rocm"]:
            score = 0.1

        # Default expectation
        if Expectations.is_default(other):
            score = 0.5

        return score