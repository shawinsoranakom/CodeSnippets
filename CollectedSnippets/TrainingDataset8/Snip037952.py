def _to_bytes(self, obj: Any, context: Optional[Context]) -> bytes:
        """Hash objects to bytes, including code with dependencies.

        Python's built in `hash` does not produce consistent results across
        runs.
        """

        if isinstance(obj, unittest.mock.Mock):
            # Mock objects can appear to be infinitely
            # deep, so we don't try to hash them at all.
            return self.to_bytes(id(obj))

        elif isinstance(obj, bytes) or isinstance(obj, bytearray):
            return obj

        elif type_util.get_fqn_type(obj) in self._hash_funcs:
            # Escape hatch for unsupported objects
            hash_func = self._hash_funcs[type_util.get_fqn_type(obj)]
            try:
                output = hash_func(obj)
            except Exception as ex:
                raise UserHashError(ex, obj, hash_func=hash_func)

            return self.to_bytes(output)

        elif isinstance(obj, str):
            return obj.encode()

        elif isinstance(obj, float):
            return self.to_bytes(hash(obj))

        elif isinstance(obj, int):
            return _int_to_bytes(obj)

        elif isinstance(obj, (list, tuple)):
            h = hashlib.new("md5")
            for item in obj:
                self.update(h, item, context)
            return h.digest()

        elif isinstance(obj, dict):
            h = hashlib.new("md5")
            for item in obj.items():
                self.update(h, item, context)
            return h.digest()

        elif obj is None:
            return b"0"

        elif obj is True:
            return b"1"

        elif obj is False:
            return b"0"

        elif type_util.is_type(obj, "pandas.core.frame.DataFrame") or type_util.is_type(
            obj, "pandas.core.series.Series"
        ):
            import pandas as pd

            if len(obj) >= _PANDAS_ROWS_LARGE:
                obj = obj.sample(n=_PANDAS_SAMPLE_SIZE, random_state=0)
            try:
                return b"%s" % pd.util.hash_pandas_object(obj).sum()
            except TypeError:
                # Use pickle if pandas cannot hash the object for example if
                # it contains unhashable objects.
                return b"%s" % pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)

        elif type_util.is_type(obj, "numpy.ndarray"):
            h = hashlib.new("md5")
            self.update(h, obj.shape)

            if obj.size >= _NP_SIZE_LARGE:
                import numpy as np

                state = np.random.RandomState(0)
                obj = state.choice(obj.flat, size=_NP_SAMPLE_SIZE)

            self.update(h, obj.tobytes())
            return h.digest()

        elif inspect.isbuiltin(obj):
            return bytes(obj.__name__.encode())

        elif any(type_util.is_type(obj, typename) for typename in _FFI_TYPE_NAMES):
            return self.to_bytes(None)

        elif type_util.is_type(obj, "builtins.mappingproxy") or type_util.is_type(
            obj, "builtins.dict_items"
        ):
            return self.to_bytes(dict(obj))

        elif type_util.is_type(obj, "builtins.getset_descriptor"):
            return bytes(obj.__qualname__.encode())

        elif isinstance(obj, UploadedFile):
            # UploadedFile is a BytesIO (thus IOBase) but has a name.
            # It does not have a timestamp so this must come before
            # temporary files
            h = hashlib.new("md5")
            self.update(h, obj.name)
            self.update(h, obj.tell())
            self.update(h, obj.getvalue())
            return h.digest()

        elif hasattr(obj, "name") and (
            isinstance(obj, io.IOBase)
            # Handle temporary files used during testing
            or isinstance(obj, tempfile._TemporaryFileWrapper)
        ):
            # Hash files as name + last modification date + offset.
            # NB: we're using hasattr("name") to differentiate between
            # on-disk and in-memory StringIO/BytesIO file representations.
            # That means that this condition must come *before* the next
            # condition, which just checks for StringIO/BytesIO.
            h = hashlib.new("md5")
            obj_name = getattr(obj, "name", "wonthappen")  # Just to appease MyPy.
            self.update(h, obj_name)
            self.update(h, os.path.getmtime(obj_name))
            self.update(h, obj.tell())
            return h.digest()

        elif isinstance(obj, Pattern):
            return self.to_bytes([obj.pattern, obj.flags])

        elif isinstance(obj, io.StringIO) or isinstance(obj, io.BytesIO):
            # Hash in-memory StringIO/BytesIO by their full contents
            # and seek position.
            h = hashlib.new("md5")
            self.update(h, obj.tell())
            self.update(h, obj.getvalue())
            return h.digest()

        elif any(
            type_util.get_fqn(x) == "sqlalchemy.pool.base.Pool"
            for x in type(obj).__bases__
        ):
            # Get connect_args from the closure of the creator function. It includes
            # arguments parsed from the URL and those passed in via `connect_args`.
            # However if a custom `creator` function is passed in then we don't
            # expect to get this data.
            cargs = obj._creator.__closure__
            cargs = [cargs[0].cell_contents, cargs[1].cell_contents] if cargs else None

            # Sort kwargs since hashing dicts is sensitive to key order
            if cargs:
                cargs[1] = dict(
                    collections.OrderedDict(
                        sorted(cargs[1].items(), key=lambda t: t[0])  # type: ignore
                    )
                )

            reduce_data = obj.__reduce__()

            # Remove thread related objects
            for attr in [
                "_overflow_lock",
                "_pool",
                "_conn",
                "_fairy",
                "_threadconns",
                "logger",
            ]:
                reduce_data[2].pop(attr, None)

            return self.to_bytes([reduce_data, cargs])

        elif type_util.is_type(obj, "sqlalchemy.engine.base.Engine"):
            # Remove the url because it's overwritten by creator and connect_args
            reduce_data = obj.__reduce__()
            reduce_data[2].pop("url", None)
            reduce_data[2].pop("logger", None)

            return self.to_bytes(reduce_data)

        elif type_util.is_type(obj, "numpy.ufunc"):
            # For numpy.remainder, this returns remainder.
            return bytes(obj.__name__.encode())

        elif type_util.is_type(obj, "socket.socket"):
            return self.to_bytes(id(obj))

        elif any(
            type_util.get_fqn(x) == "torch.nn.modules.module.Module"
            for x in type(obj).__bases__
        ):
            return self.to_bytes(id(obj))

        elif type_util.is_type(obj, "tensorflow.python.client.session.Session"):
            return self.to_bytes(id(obj))

        elif type_util.is_type(obj, "torch.Tensor") or type_util.is_type(
            obj, "torch._C._TensorBase"
        ):
            return self.to_bytes([obj.detach().numpy(), obj.grad])

        elif any(type_util.is_type(obj, typename) for typename in _KERAS_TYPE_NAMES):
            return self.to_bytes(id(obj))

        elif type_util.is_type(
            obj,
            "tensorflow.python.saved_model.load.Loader._recreate_base_user_object.<locals>._UserObject",
        ):
            return self.to_bytes(id(obj))

        elif inspect.isroutine(obj):
            wrapped = getattr(obj, "__wrapped__", None)
            if wrapped is not None:
                # Ignore the wrapper of wrapped functions.
                return self.to_bytes(wrapped)

            if obj.__module__.startswith("streamlit"):
                # Ignore streamlit modules even if they are in the CWD
                # (e.g. during development).
                return self.to_bytes("%s.%s" % (obj.__module__, obj.__name__))

            h = hashlib.new("md5")

            code = getattr(obj, "__code__", None)
            assert code is not None
            if self._file_should_be_hashed(code.co_filename):
                context = _get_context(obj)
                defaults = getattr(obj, "__defaults__", None)
                if defaults is not None:
                    self.update(h, defaults, context)
                h.update(self._code_to_bytes(code, context, func=obj))
            else:
                # Don't hash code that is not in the current working directory.
                self.update(h, obj.__module__)
                self.update(h, obj.__name__)
            return h.digest()

        elif inspect.iscode(obj):
            if context is None:
                raise RuntimeError("context must be defined when hashing code")
            return self._code_to_bytes(obj, context)

        elif inspect.ismodule(obj):
            # TODO: Figure out how to best show this kind of warning to the
            # user. In the meantime, show nothing. This scenario is too common,
            # so the current warning is quite annoying...
            # st.warning(('Streamlit does not support hashing modules. '
            #             'We did not hash `%s`.') % obj.__name__)
            # TODO: Hash more than just the name for internal modules.
            return self.to_bytes(obj.__name__)

        elif inspect.isclass(obj):
            # TODO: Figure out how to best show this kind of warning to the
            # user. In the meantime, show nothing. This scenario is too common,
            # (e.g. in every "except" statement) so the current warning is
            # quite annoying...
            # st.warning(('Streamlit does not support hashing classes. '
            #             'We did not hash `%s`.') % obj.__name__)
            # TODO: Hash more than just the name of classes.
            return self.to_bytes(obj.__name__)

        elif isinstance(obj, functools.partial):
            # The return value of functools.partial is not a plain function:
            # it's a callable object that remembers the original function plus
            # the values you pickled into it. So here we need to special-case it.
            h = hashlib.new("md5")
            self.update(h, obj.args)
            self.update(h, obj.func)
            self.update(h, obj.keywords)
            return h.digest()

        else:
            # As a last resort, hash the output of the object's __reduce__ method
            h = hashlib.new("md5")
            try:
                reduce_data = obj.__reduce__()
            except Exception as ex:
                raise UnhashableTypeError(ex, obj)

            for item in reduce_data:
                self.update(h, item, context)
            return h.digest()