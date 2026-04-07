def __int__(self):
        raise TypeError(
            "Cannot cast AnonymousUser to int. Are you trying to use it in place of "
            "User?"
        )