def __getstate__(self):
        state = super().__getstate__()
        state.pop("related_model", None)
        return state