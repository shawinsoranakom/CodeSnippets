def hierarchical_pickle(data):
    if isinstance(data, (bool, int, float, str, type(None))):
        return data
    if isinstance(data, list):
        return [hierarchical_pickle(d) for d in data]
    if isinstance(data, tuple):
        return {
            "__tuple_values__": hierarchical_pickle(list(data)),
        }
    if isinstance(data, dict):
        return {
            "__is_dict__": True,
            "keys": hierarchical_pickle(list(data.keys())),
            "values": hierarchical_pickle(list(data.values())),
        }
    if isinstance(data, torch.utils.show_pickle.FakeObject):
        typename = f"{data.module}.{data.name}"
        if (
            typename.startswith(('__torch__.', 'torch.jit.LoweredWrapper.', 'torch.jit.LoweredModule.'))
        ):
            if data.args != ():
                raise AssertionError("data.args is not ()")
            return {
                "__module_type__": typename,
                "state": hierarchical_pickle(data.state),
            }
        if typename == "torch._utils._rebuild_tensor_v2":
            if data.state is not None:
                raise AssertionError("data.state is not None")
            storage, offset, size, stride, requires_grad, *_ = data.args
            storage_info = get_storage_info(storage)
            return {"__tensor_v2__": [storage_info, offset, size, stride, requires_grad]}
        if typename == "torch._utils._rebuild_qtensor":
            if data.state is not None:
                raise AssertionError("data.state is not None")
            storage, offset, size, stride, quantizer, requires_grad, *_ = data.args
            storage_info = get_storage_info(storage)
            if not isinstance(quantizer, tuple):
                raise AssertionError("quantizer is not a tuple")
            if not isinstance(quantizer[0], torch.utils.show_pickle.FakeClass):
                raise AssertionError("quantizer[0] is not a FakeClass")
            if quantizer[0].module != "torch":
                raise AssertionError("quantizer[0].module is not torch")
            if quantizer[0].name == "per_tensor_affine":
                if len(quantizer) != 3:
                    raise AssertionError("len(quantizer) is not 3")
                if not isinstance(quantizer[1], float):
                    raise AssertionError("quantizer[1] is not a float")
                if not isinstance(quantizer[2], int):
                    raise AssertionError("quantizer[2] is not an int")
                quantizer_extra = list(quantizer[1:3])
            else:
                quantizer_extra = []
            quantizer_json = [quantizer[0].name] + quantizer_extra
            return {"__qtensor__": [storage_info, offset, size, stride, quantizer_json, requires_grad]}
        if typename == "torch.jit._pickle.restore_type_tag":
            if data.state is not None:
                raise AssertionError("data.state is not None")
            obj, typ = data.args
            if not isinstance(typ, str):
                raise AssertionError("typ is not a string")
            return hierarchical_pickle(obj)
        if re.fullmatch(r"torch\.jit\._pickle\.build_[a-z]+list", typename):
            if data.state is not None:
                raise AssertionError("data.state is not None")
            ls, = data.args
            if not isinstance(ls, list):
                raise AssertionError("ls is not a list")
            return hierarchical_pickle(ls)
        if typename == "torch.device":
            if data.state is not None:
                raise AssertionError("data.state is not None")
            name, = data.args
            if not isinstance(name, str):
                raise AssertionError("name is not a string")
            # Just forget that it was a device and return the name.
            return name
        if typename == "builtin.UnicodeDecodeError":
            if data.state is not None:
                raise AssertionError("data.state is not None")
            msg, = data.args
            if not isinstance(msg, str):
                raise AssertionError("msg is not a string")
            # Hack: Pretend this is a module so we don't need custom serialization.
            # Hack: Wrap the message in a tuple so it looks like a nice state object.
            # TODO: Undo at least that second hack.  We should support string states.
            return {
                "__module_type__": typename,
                "state": hierarchical_pickle((msg,)),
            }
        raise Exception(f"Can't prepare fake object of type for JS: {typename}")  # noqa: TRY002
    raise Exception(f"Can't prepare data of type for JS: {type(data)}")