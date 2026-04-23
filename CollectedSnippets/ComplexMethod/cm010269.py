def replace_all_uses(self, old: str, new: str):
        """
        Replace all uses of the old name with new name in the signature.
        """
        if not isinstance(old, str):
            raise AssertionError(f"expected old to be str, got {type(old)}")
        if not isinstance(new, str):
            raise AssertionError(f"expected new to be str, got {type(new)}")
        arg_types = (
            TensorArgument,
            SymIntArgument,
            SymFloatArgument,
            SymBoolArgument,
            CustomObjArgument,
            TokenArgument,
        )
        for o in self.output_specs:
            if isinstance(o.arg, arg_types):
                if o.arg.name == old:
                    o.arg.name = new
        for i in self.input_specs:
            if isinstance(i.arg, arg_types):
                if i.arg.name == old:
                    i.arg.name = new