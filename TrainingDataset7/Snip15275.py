def __getattr__(self, item):
                if item == "dynamic_method":

                    @admin.display
                    def method(obj):
                        pass

                    return method
                raise AttributeError