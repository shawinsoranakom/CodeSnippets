def __getstate__(self):
                state = super().__getstate__().copy()
                del state["dont_pickle"]
                return state