def _main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0] if sys.argv else " "} OUTDIR [loops]")
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    functions = [
        func
        for func in globals().values()
        if isinstance(func, FunctionType) and not func.__name__.startswith("_")
    ]
    for func in functions:
        _run_and_dump(func, n, outdir)