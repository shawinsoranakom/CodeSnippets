def build(self, args, root=True):
        if args is None or len(args) == 0:
            return None
        elif isinstance(args, list):
            if root:
                sequence = [self.build(value, root=False) for value in args]
                return iaa.Sequential(sequence)
            else:
                return getattr(iaa, args[0])(
                    *[self.to_tuple_if_list(a) for a in args[1:]]
                )
        elif isinstance(args, dict):
            cls = getattr(iaa, args["type"])
            return cls(**{k: self.to_tuple_if_list(v) for k, v in args["args"].items()})
        else:
            raise RuntimeError("unknown augmenter arg: " + str(args))