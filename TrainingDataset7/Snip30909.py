def __getstate__(self):
        state = super().__getstate__()
        state[DJANGO_VERSION_PICKLE_KEY] = "1.0"
        return state