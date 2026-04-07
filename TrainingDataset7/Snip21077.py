def get_default_r():
    return R.objects.get_or_create(is_default=True)[0].pk