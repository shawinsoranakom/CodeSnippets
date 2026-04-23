def _generate_examples(self, typ):
        if typ is int:
            return [17]
        if typ is float:
            return [3.14]
        if typ is bool:
            return [True]
        if typ is str:
            return ["foo"]
        if torch.distributed.is_available():
            from torch.distributed.distributed_c10d import GroupName

            if typ is GroupName:
                return ["group"]
        if typ is torch.dtype:
            return [torch.float32]
        if typ is torch.device:
            return [torch.device("cpu")]
        if typ == torch.types.Number:
            return [2.718]
        if typ is torch.Tensor:
            return [torch.tensor(3)]
        if typ == Optional[torch.types.Number]:
            return [None, 2.718]
        origin = typing.get_origin(typ)
        if origin is Union:
            args = typing.get_args(typ)
            if not (
                len(args) == 2 and (args[0] is type(None) or args[1] is type(None))
            ):
                raise AssertionError(f"expected Optional type, got {args}")
            elt = args[0] if args[1] is type(None) else args[1]
            return self._generate_examples(elt) + [None]
        if origin is list:
            args = typing.get_args(typ)
            if len(args) != 1:
                raise AssertionError(f"expected list with 1 arg, got {len(args)}")
            elt = args[0]
            return [
                self._generate_examples(elt),
                self._generate_examples(elt),
                self._generate_examples(elt),
            ]
        if origin is collections.abc.Sequence:
            args = typing.get_args(typ)
            if len(args) != 1:
                raise AssertionError(f"expected Sequence with 1 arg, got {len(args)}")
            examples = self._generate_examples(args[0])
            return list(itertools.product(examples, examples)) + []
        raise NotImplementedError(
            f"testrunner cannot generate instanstance of type {typ}"
        )