def __reduce__(self):
                reduce_list = super().__reduce__()
                data = reduce_list[-1]
                del data[DJANGO_VERSION_PICKLE_KEY]
                return reduce_list