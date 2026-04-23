def inner(self, *args):
            signature = inspect.signature(func)
            for tag_name, setup_func in tags.items():
                if "tag_name" in signature.parameters:
                    setup_func(partial(func, tag_name=tag_name))(self)
                else:
                    setup_func(func)(self)