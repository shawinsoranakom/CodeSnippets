def load(self):
        """Read a pickled object representation from the open file.

        Return the reconstituted object hierarchy specified in the file.
        """
        self.metastack = []
        self.stack: list[Any] = []
        self.append = self.stack.append
        read = self.read
        while True:
            key = read(1)
            if not key:
                raise EOFError
            if not isinstance(key, bytes_types):
                raise AssertionError(f"Expected bytes, got {type(key).__name__}")
            # Risky operators
            if key[0] == GLOBAL[0]:
                module, name = _read_global_instruction(self.readline)
                full_path = f"{module}.{name}"
                if module in _blocklisted_modules:
                    raise UnpicklingError(
                        f"Trying to load unsupported GLOBAL {full_path} whose module {module} is blocked."
                    )
                if full_path in _get_allowed_globals():
                    self.append(_get_allowed_globals()[full_path])
                elif full_path in _get_user_allowed_globals():
                    self.append(_get_user_allowed_globals()[full_path])
                elif full_path in (
                    [
                        "torch.nested._internal.nested_tensor.NestedTensor",
                        "torch.nested._internal.nested_tensor._rebuild_njt",
                        "torch._dynamo.decorators._DimRange",
                    ]
                ):
                    raise UnpicklingError(
                        "``torch.nested`` and ``torch._dynamo`` must be imported to load nested jagged tensors (NJTs)"
                    )
                elif full_path in (
                    [
                        "torch.distributed.device_mesh.DeviceMesh",
                        "torch.distributed.tensor._dtensor_spec.DTensorSpec",
                        "torch.distributed.tensor._dtensor_spec.TensorMeta",
                        "torch.distributed.tensor.DTensor",
                        "torch.distributed.tensor.placement_types.Partial",
                        "torch.distributed.tensor.placement_types.Replicate",
                        "torch.distributed.tensor.placement_types.Shard",
                    ]
                ):
                    raise UnpicklingError(
                        "``torch.distributed.tensor`` must be imported to load DTensors"
                    )
                else:
                    builtins_name = "builtins"
                    if (
                        builtins_name in full_path
                        and builtins_name == full_path[: len(builtins_name)]
                    ):
                        full_path = full_path[len(builtins_name) :]
                        full_path = (
                            full_path[1:]
                            if len(full_path) > 0 and full_path[0] == "."
                            else builtins_name + full_path
                        )
                    raise UnpicklingError(
                        f"Unsupported global: GLOBAL {full_path} was not an allowed global by default. "
                        f"Please use `torch.serialization.add_safe_globals([{full_path}])` or the "
                        f"`torch.serialization.safe_globals([{full_path}])` context manager to allowlist this global "
                        "if you trust this class/function."
                    )
            elif key[0] == NEWOBJ[0]:
                args = self.stack.pop()
                cls = self.stack.pop()
                if cls is torch.nn.Parameter:
                    self.append(torch.nn.Parameter(*args))
                elif (
                    cls in _get_user_allowed_globals().values()
                    or cls in _get_allowed_globals().values()
                ):
                    result = cls.__new__(cls, *args)
                    if cls in torch._tensor_classes and "sparse" in cls.__module__:
                        _sparse_tensors_to_validate.append(result)
                    self.append(result)
                else:
                    raise UnpicklingError(
                        "Can only create new object for nn.Parameter or classes allowlisted "
                        f"via `add_safe_globals` but got {cls}"
                    )
            elif key[0] == REDUCE[0]:
                args = self.stack.pop()
                func = self.stack[-1]
                if (
                    func not in _get_allowed_globals().values()
                    and func not in _get_user_allowed_globals().values()
                ):
                    error_msg = (
                        f"Trying to call reduce for unrecognized function {func}"
                    )
                    if hasattr(func, "__self__"):
                        error_msg += f" which belongs to {func.__self__}"
                    raise UnpicklingError(error_msg)
                result = func(*args)
                if func in torch._tensor_classes and "sparse" in func.__module__:
                    _sparse_tensors_to_validate.append(result)
                self.stack[-1] = result
            elif key[0] == BUILD[0]:
                state = self.stack.pop()
                inst = self.stack[-1]
                if type(inst) is torch.Tensor:
                    # Legacy unpickling

                    inst.set_(*state)
                elif type(inst) is torch.nn.Parameter:
                    inst.__setstate__(state)
                elif type(inst) is OrderedDict:
                    inst.__dict__.update(state)
                elif (
                    type(inst) in _get_user_allowed_globals().values()
                    or type(inst) in _get_allowed_globals().values()
                ):
                    if hasattr(inst, "__setstate__"):
                        inst.__setstate__(state)
                    else:
                        # mimics load_build in pickle
                        # https://github.com/python/cpython/blob/f0c6fccd08904787a39269367f09f263d496114c/Lib/pickle.py#L1854-L1867
                        slotstate = None
                        if isinstance(state, tuple) and len(state) == 2:
                            state, slotstate = state
                        if state:
                            inst.__dict__.update(state)
                        if slotstate:
                            for k, v in slotstate.items():
                                setattr(inst, k, v)
                else:
                    raise UnpicklingError(
                        "Can only build Tensor, Parameter, OrderedDict or types allowlisted "
                        f"via `add_safe_globals`, but got {type(inst)}"
                    )
            # Stack manipulation
            elif key[0] == APPEND[0]:
                item = self.stack.pop()
                list_obj = self.stack[-1]
                if type(list_obj) is not list:
                    raise UnpicklingError(
                        f"Can only append to lists, but got {type(list_obj)}"
                    )
                list_obj.append(item)
            elif key[0] == APPENDS[0]:
                items = self.pop_mark()
                list_obj = self.stack[-1]
                if type(list_obj) is not list:
                    raise UnpicklingError(
                        f"Can only extend lists, but got {type(list_obj)}"
                    )
                list_obj.extend(items)
            elif key[0] == SETITEM[0]:
                (v, k) = (self.stack.pop(), self.stack.pop())
                self._check_set_item_target("SETITEM")
                self.stack[-1][k] = v
            elif key[0] == SETITEMS[0]:
                items = self.pop_mark()
                self._check_set_item_target("SETITEMS")
                for i in range(0, len(items), 2):
                    self.stack[-1][items[i]] = items[i + 1]
            elif key[0] == MARK[0]:
                self.metastack.append(self.stack)
                self.stack = []
                self.append = self.stack.append
            elif key[0] == TUPLE[0]:
                items = self.pop_mark()
                self.append(tuple(items))
            elif key[0] == TUPLE1[0]:
                self.stack[-1] = (self.stack[-1],)
            elif key[0] == TUPLE2[0]:
                self.stack[-2:] = [(self.stack[-2], self.stack[-1])]
            elif key[0] == TUPLE3[0]:
                self.stack[-3:] = [(self.stack[-3], self.stack[-2], self.stack[-1])]
            # Basic types construction
            elif key[0] == NONE[0]:
                self.append(None)
            elif key[0] == NEWFALSE[0]:
                self.append(False)
            elif key[0] == NEWTRUE[0]:
                self.append(True)
            elif key[0] == EMPTY_TUPLE[0]:
                self.append(())
            elif key[0] == EMPTY_LIST[0]:
                self.append([])
            elif key[0] == EMPTY_DICT[0]:
                self.append({})
            elif key[0] == EMPTY_SET[0]:
                self.append(set())
            elif key[0] == BININT[0]:
                self.append(unpack("<i", read(4))[0])
            elif key[0] == BININT1[0]:
                self.append(self.read(1)[0])
            elif key[0] == BININT2[0]:
                self.append(unpack("<H", read(2))[0])
            elif key[0] == BINFLOAT[0]:
                self.append(unpack(">d", self.read(8))[0])
            elif key[0] == BINUNICODE[0]:
                strlen = unpack("<I", read(4))[0]
                if strlen > maxsize:
                    raise UnpicklingError("String is too long")
                strval = str(read(strlen), "utf-8", "surrogatepass")
                self.append(strval)
            elif key[0] == SHORT_BINSTRING[0]:
                strlen = read(1)[0]
                strdata = read(strlen)
                if self.encoding != "bytes":
                    strdata = strdata.decode(self.encoding, "strict")
                self.append(strdata)
            elif key[0] == BINPERSID[0]:
                pid = self.stack.pop()
                # Only allow persistent load of storage
                if type(pid) is not tuple and type(pid) is not int:
                    raise UnpicklingError(
                        f"persistent_load id must be tuple or int, but got {type(pid)}"
                    )
                if (
                    type(pid) is tuple
                    and len(pid) > 0
                    and torch.serialization._maybe_decode_ascii(pid[0]) != "storage"
                ):
                    raise UnpicklingError(
                        f"Only persistent_load of storage is allowed, but got {type(pid[0])}"
                    )
                self.append(self.persistent_load(pid))
            elif key[0] in [BINGET[0], LONG_BINGET[0]]:
                idx = (read(1) if key[0] == BINGET[0] else unpack("<I", read(4)))[0]
                self.append(self.memo[idx])
            elif key[0] in [BINPUT[0], LONG_BINPUT[0]]:
                i = (read(1) if key[0] == BINPUT[0] else unpack("<I", read(4)))[0]
                if i < 0:
                    raise ValueError("negative argument")
                self.memo[i] = self.stack[-1]
            elif key[0] == LONG1[0]:
                n = read(1)[0]
                data = read(n)
                self.append(decode_long(data))
            # First and last deserializer ops
            elif key[0] == PROTO[0]:
                self.proto = read(1)[0]
                if self.proto != 2:
                    warnings.warn(
                        f"Detected pickle protocol {self.proto} in the checkpoint, which was "
                        "not the default pickle protocol used by `torch.load` (2). The weights_only "
                        "Unpickler might not support all instructions implemented by this protocol, "
                        "please file an issue for adding support if you encounter this.",
                        stacklevel=2,
                    )
            elif key[0] == STOP[0]:
                rc = self.stack.pop()
                return rc
            else:
                raise UnpicklingError(f"Unsupported operand {key[0]}")