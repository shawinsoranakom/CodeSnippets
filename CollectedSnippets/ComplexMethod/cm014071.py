def initialize(
        self,
        fn: Any,
        dynamo: _DynamoCacheEntry | None = None,
        ignore_inlined_sources: bool = False,
    ) -> None:
        from .eval_frame import innermost_fn

        assert not self._initialized
        self._source_info = SourceInfo(inlined_sources=set())
        self._innermost_fn = innermost_fn(fn)  # type: ignore[assignment]
        assert self._innermost_fn is not None
        if dynamo is not None:
            assert isinstance(dynamo, _DynamoCacheEntry)
            dynamo.check_versions()
            if not ignore_inlined_sources:
                for code in dynamo.source_info.inlined_sources:
                    m = importlib.import_module(code.module)
                    checksum = _hash_sourcelines(m, code.firstlineno, code.lastlineno)
                    if checksum != code.checksum:
                        raise RuntimeError(
                            f"Source code changes detected for {code.module} (line {code.firstlineno} - line {code.lastlineno})"
                        )

                self._source_info = dynamo.source_info

            main, *codes = dynamo.codes
            self._codes = {self._innermost_fn.__code__: main}
            for code in codes:
                self._codes[SerializedCode.to_code_object(code.python_code)] = code
        else:
            self._add_function(
                self._innermost_fn.__code__, self._innermost_fn.__module__
            )
        self._initialized = True