def convert_schedule_to_cron(schedule):
        """Convert Events schedule like "cron(0 20 * * ? *)" or "rate(5 minutes)" """
        cron_regex = r"\s*cron\s*\(([^\)]*)\)\s*"
        if re.match(cron_regex, schedule):
            cron = re.sub(cron_regex, r"\1", schedule)
            return cron
        rate_regex = r"\s*rate\s*\(([^\)]*)\)\s*"
        if re.match(rate_regex, schedule):
            rate = re.sub(rate_regex, r"\1", schedule)
            value, unit = re.split(r"\s+", rate.strip())

            value = int(value)
            if value < 1:
                raise ValueError("Rate value must be larger than 0")
            # see https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rate-expressions.html
            if value == 1 and unit.endswith("s"):
                raise ValueError("If the value is equal to 1, then the unit must be singular")
            if value > 1 and not unit.endswith("s"):
                raise ValueError("If the value is greater than 1, the unit must be plural")

            if "minute" in unit:
                return f"*/{value} * * * *"
            if "hour" in unit:
                return f"0 */{value} * * *"
            if "day" in unit:
                return f"0 0 */{value} * *"
            raise ValueError(f"Unable to parse events schedule expression: {schedule}")
        return schedule