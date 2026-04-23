def _to_naive(value):
    if timezone.is_aware(value):
        value = timezone.make_naive(value, datetime.UTC)
    return value