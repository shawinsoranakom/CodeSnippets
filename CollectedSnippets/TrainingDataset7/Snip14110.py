def get_mod_func(callback):
    # Convert 'django.views.news.stories.story_detail' to
    # ['django.views.news.stories', 'story_detail']
    try:
        dot = callback.rindex(".")
    except ValueError:
        return callback, ""
    return callback[:dot], callback[dot + 1 :]