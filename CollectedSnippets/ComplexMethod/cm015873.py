def wrap_test_class(orig_cls):
    dct = orig_cls.__dict__.copy()
    for name in list(dct.keys()):
        fn = dct[name]
        if not callable(fn) or name in skipped_tests:
            continue
        elif (
            xfail_re.match(name)
            or name in xfail_by_backend["ca_eager"]
            or name in xfail_divergence_from_eager
        ):
            dct[name] = unittest.expectedFailure
        elif name.startswith("test_"):
            backend = lookup_backend(name)
            if not HAS_CUDA_AND_TRITON and backend == "inductor":
                continue
            ctxs = [
                compiled_autograd._enable(
                    make_compiler_fn(
                        backend=backend,
                        fullgraph=name not in known_graph_breaks_tests,
                    )
                ),
                test_contexts.get(name, contextlib.nullcontext()),
            ]
            dct[name] = make_wrapped(fn, ctxs)

    cls = type(
        orig_cls.__name__ + "WithCompiledAutograd",
        (orig_cls,),
        dct,
    )
    cls.__file__ = __file__
    return cls