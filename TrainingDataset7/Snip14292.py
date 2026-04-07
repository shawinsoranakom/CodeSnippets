def __init__(self, obj):
        self.data = obj
        self.timezone = None

        if isinstance(obj, datetime):
            # Timezone is only supported when formatting datetime objects, not
            # date objects (timezone information not appropriate), or time
            # objects (against established django policy).
            if is_naive(obj):
                timezone = get_default_timezone()
            else:
                timezone = obj.tzinfo
            if not _datetime_ambiguous_or_imaginary(obj, timezone):
                self.timezone = timezone