def check_async_unsafe(app_configs, **kwargs):
    if os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE"):
        return [E001]
    return []