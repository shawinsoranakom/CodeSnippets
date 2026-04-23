def convert_schedule_to_cron(schedule):
    """Convert Events schedule like "cron(0 20 * * ? *)" or "rate(5 minutes)" """
    cron_match = CRON_REGEX.match(schedule)
    if cron_match:
        return cron_match.group(1)

    rate_match = RATE_REGEX.match(schedule)
    if rate_match:
        rate = rate_match.group(1)
        rate_value, rate_unit = re.split(r"\s+", rate.strip())
        rate_value = int(rate_value)

        if rate_value < 1:
            raise ValueError("Rate value must be larger than 0")
        # see https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rate-expressions.html
        if rate_value == 1 and rate_unit.endswith("s"):
            raise ValueError("If the value is equal to 1, then the unit must be singular")
        if rate_value > 1 and not rate_unit.endswith("s"):
            raise ValueError("If the value is greater than 1, the unit must be plural")

        if "minute" in rate_unit:
            return f"*/{rate_value} * * * *"
        if "hour" in rate_unit:
            return f"0 */{rate_value} * * *"
        if "day" in rate_unit:
            return f"0 0 */{rate_value} * *"

        # TODO: cover via test
        # raise ValueError(f"Unable to parse events schedule expression: {schedule}")

    return schedule