def __getstate__(self):
        state = super().__getstate__()
        del state[DJANGO_VERSION_PICKLE_KEY]
        return state