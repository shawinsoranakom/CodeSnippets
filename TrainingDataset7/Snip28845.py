def __reduce__(self):
                reduce_list = super().__reduce__()
                data = reduce_list[-1]
                data[DJANGO_VERSION_PICKLE_KEY] = "1.0"
                return reduce_list