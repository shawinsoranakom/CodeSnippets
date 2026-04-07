def string_for(cls, value):
        if not isinstance(value, date):  # datetime is a subclass of date
            return value

        now = datetime.now(UTC if is_aware(value) else None)
        if value < now:
            delta = now - value
            if delta.days != 0:
                return cls.time_strings["past-day"] % {
                    "delta": defaultfilters.timesince(
                        value, now, time_strings=cls.past_substrings
                    ),
                }
            elif delta.seconds == 0:
                return cls.time_strings["now"]
            elif delta.seconds < 60:
                return cls.time_strings["past-second"] % {"count": delta.seconds}
            elif delta.seconds // 60 < 60:
                count = delta.seconds // 60
                return cls.time_strings["past-minute"] % {"count": count}
            else:
                count = delta.seconds // 60 // 60
                return cls.time_strings["past-hour"] % {"count": count}
        else:
            delta = value - now
            if delta.days != 0:
                return cls.time_strings["future-day"] % {
                    "delta": defaultfilters.timeuntil(
                        value, now, time_strings=cls.future_substrings
                    ),
                }
            elif delta.seconds == 0:
                return cls.time_strings["now"]
            elif delta.seconds < 60:
                return cls.time_strings["future-second"] % {"count": delta.seconds}
            elif delta.seconds // 60 < 60:
                count = delta.seconds // 60
                return cls.time_strings["future-minute"] % {"count": count}
            else:
                count = delta.seconds // 60 // 60
                return cls.time_strings["future-hour"] % {"count": count}