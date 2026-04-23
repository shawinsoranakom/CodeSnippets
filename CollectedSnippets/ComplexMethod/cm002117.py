def test_auto_docstring_import_time_upper_bound(self):
        """
        Asserts that auto_docstring overhead stays below a percentage of total
        import time.

        Method
        ------
        1. Collect ``modeling_*.py``, ``image_processing_*.py``, ``processing_*.py``
           under ``transformers/models``, then sample every 10th for speed.
        2. Warmup: import the sampled modules once so Python's bytecode cache is hot.
        3. Measure WITH auto_docstring: clear cache, re-import, median over 5 runs.
        4. Measure WITHOUT auto_docstring: noop-patch, clear cache, re-import, median.
        5. cost_pct = (real - noop) / real * 100; assert cost_pct < upper bound.
        """
        if "transformers.utils" not in sys.modules:
            importlib.import_module("transformers.utils")
        _utils_module = sys.modules["transformers.utils"]

        src_root = Path(__file__).resolve().parent.parent.parent / "src"
        models_dir = src_root / "transformers" / "models"
        all_modules: list[str] = []
        for pattern in ("modeling_*.py", "image_processing_*.py", "processing_*.py"):
            for f in sorted(models_dir.rglob(pattern)):
                rel = f.with_suffix("").relative_to(src_root)
                all_modules.append(".".join(rel.parts))
        model_modules = all_modules[::10]

        def _clear():
            for key in [k for k in sys.modules if k.startswith("transformers.models")]:
                del sys.modules[key]

        def _import_all():
            for mod in model_modules:
                try:
                    importlib.import_module(mod)
                except Exception:
                    continue

        _import_all()  # warmup

        # With auto_docstring (real)
        times_real: list[float] = []
        for _ in range(5):
            _clear()
            t0 = time.perf_counter()
            _import_all()
            times_real.append(time.perf_counter() - t0)

        # Without auto_docstring (noop patch)
        _orig = _utils_module.auto_docstring
        _noop = lambda x=None, **kw: (lambda f: f) if x is None else x  # noqa: E731
        times_noop: list[float] = []
        for _ in range(5):
            _utils_module.auto_docstring = _noop
            try:
                _clear()
                t0 = time.perf_counter()
                _import_all()
                times_noop.append(time.perf_counter() - t0)
            finally:
                _utils_module.auto_docstring = _orig

        median_real = statistics.median(times_real)
        median_noop = statistics.median(times_noop)
        cost_pct = (median_real - median_noop) / median_real * 100 if median_real > 0 else 0.0
        print(f"Cost percentage: {cost_pct:.1f}%")
        assert cost_pct < self.AUTO_DOCSTRING_COST_PCT_UPPER_BOUND, (
            f"auto_docstring cost {cost_pct:.1f}% of import time exceeds upper bound "
            f"{self.AUTO_DOCSTRING_COST_PCT_UPPER_BOUND}% "
            f"({len(model_modules)} of {len(all_modules)} modules)"
        )