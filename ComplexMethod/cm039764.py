def patch_lazy_xp_functions(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch | None = None,
    *,
    xp: ModuleType,
) -> contextlib.AbstractContextManager[None]:
    """
    Test lazy execution of functions tagged with :func:`lazy_xp_function`.

    If ``xp==jax.numpy``, search for all functions which have been tagged with
    :func:`lazy_xp_function` in the globals of the module that defines the current test,
    as well as in the ``lazy_xp_modules`` list in the globals of the same module,
    and wrap them with :func:`jax.jit`. Unwrap them at the end of the test.

    If ``xp==dask.array``, wrap the functions with a decorator that disables
    ``compute()`` and ``persist()`` and ensures that exceptions and warnings are raised
    eagerly.

    This function should be typically called by your library's `xp` fixture that runs
    tests on multiple backends::

        @pytest.fixture(params=[
            numpy,
            array_api_strict,
            pytest.param(jax.numpy, marks=pytest.mark.thread_unsafe),
            pytest.param(dask.array, marks=pytest.mark.thread_unsafe),
        ])
        def xp(request):
            with patch_lazy_xp_functions(request, xp=request.param):
                yield request.param

    but it can be otherwise be called by the test itself too.

    Parameters
    ----------
    request : pytest.FixtureRequest
        Pytest fixture, as acquired by the test itself or by one of its fixtures.
    monkeypatch : pytest.MonkeyPatch
        Deprecated
    xp : array_namespace
        Array namespace to be tested.

    See Also
    --------
    lazy_xp_function : Tag a function to be tested on lazy backends.
    pytest.FixtureRequest : `request` test function parameter.

    Notes
    -----
    This context manager monkey-patches modules and as such is thread unsafe
    on Dask and JAX. If you run your test suite with
    `pytest-run-parallel <https://github.com/Quansight-Labs/pytest-run-parallel/>`_,
    you should mark these backends with ``@pytest.mark.thread_unsafe``, as shown in
    the example above.
    """
    mod = cast(ModuleType, request.module)
    mods = [mod, *cast(list[ModuleType], getattr(mod, "lazy_xp_modules", []))]

    to_revert: list[tuple[ModuleType, str, object]] = []

    def temp_setattr(mod: ModuleType, name: str, func: object) -> None:
        """
        Variant of monkeypatch.setattr, which allows monkey-patching only selected
        parameters of a test so that pytest-run-parallel can run on the remainder.
        """
        assert hasattr(mod, name)
        to_revert.append((mod, name, getattr(mod, name)))
        setattr(mod, name, func)

    if monkeypatch is not None:
        warnings.warn(
            (
                "The `monkeypatch` parameter is deprecated and will be removed in a "
                "future version. "
                "Use `patch_lazy_xp_function` as a context manager instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        # Enable using patch_lazy_xp_function not as a context manager
        temp_setattr = monkeypatch.setattr  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]

    def iter_tagged() -> Iterator[
        tuple[ModuleType, str, Callable[..., Any], dict[str, Any]]
    ]:
        for mod in mods:
            for name, func in mod.__dict__.items():
                tags: dict[str, Any] | None = None
                with contextlib.suppress(AttributeError):
                    tags = func._lazy_xp_function  # pylint: disable=protected-access
                if tags is None:
                    with contextlib.suppress(KeyError, TypeError):
                        tags = _ufuncs_tags[func]
                if tags is not None:
                    yield mod, name, func, tags

    if is_dask_namespace(xp):
        for mod, name, func, tags in iter_tagged():
            n = tags["allow_dask_compute"]
            if n is True:
                n = 1_000_000
            elif n is False:
                n = 0
            wrapped = _dask_wrap(func, n)
            temp_setattr(mod, name, wrapped)

    elif is_jax_namespace(xp):
        for mod, name, func, tags in iter_tagged():
            if tags["jax_jit"]:
                wrapped = jax_autojit(func)
                temp_setattr(mod, name, wrapped)

    # We can't just decorate patch_lazy_xp_functions with
    # @contextlib.contextmanager because it would not work with the
    # deprecated monkeypatch when not used as a context manager.
    @contextlib.contextmanager
    def revert_on_exit() -> Generator[None]:
        try:
            yield
        finally:
            for mod, name, orig_func in to_revert:
                setattr(mod, name, orig_func)

    return revert_on_exit()