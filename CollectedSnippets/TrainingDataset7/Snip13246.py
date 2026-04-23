def update(self, other_dict):
        "Push other_dict to the stack of dictionaries in the Context"
        if not hasattr(other_dict, "__getitem__"):
            raise TypeError("other_dict must be a mapping (dictionary-like) object.")
        if isinstance(other_dict, BaseContext):
            other_dict = other_dict.dicts[1:].pop()
        return ContextDict(self, other_dict)