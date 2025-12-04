def benchmark() -> None:
    from timeit import timeit

    print("Running performance benchmarks...")
    setup = "from string import printable ; from __main__ import atbash, atbash_slow"
    print(f"> atbash_slow(): {timeit('atbash_slow(printable)', setup=setup)} seconds")
    print(f">      atbash(): {timeit('atbash(printable)', setup=setup)} seconds")
