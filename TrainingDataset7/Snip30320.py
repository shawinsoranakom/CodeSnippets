def make_handler(model, event):
            def _handler(*args, **kwargs):
                output.append("%s %s save" % (model, event))

            return _handler