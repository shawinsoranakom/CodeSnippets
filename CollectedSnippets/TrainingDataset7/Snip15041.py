def run(*args, verbosity=0, **kwargs):
    if verbosity > 1:
        print(f"\n** subprocess.run ** command: {args=} {kwargs=}")
    return subprocess.run(*args, **kwargs)