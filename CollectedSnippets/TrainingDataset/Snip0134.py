def benchmark() -> None:

    def do_benchmark(number: int) -> None:
        setup = "import __main__ as z"
        print(f"Benchmark when {number = }:")
        print(f"{get_set_bits_count_using_modulo_operator(number) = }")
        timing = timeit(
            f"z.get_set_bits_count_using_modulo_operator({number})", setup=setup
        )
        print(f"timeit() runs in {timing} seconds")
        print(f"{get_set_bits_count_using_brian_kernighans_algorithm(number) = }")
        timing = timeit(
            f"z.get_set_bits_count_using_brian_kernighans_algorithm({number})",
            setup=setup,
        )
        print(f"timeit() runs in {timing} seconds")

    for number in (25, 37, 58, 0):
        do_benchmark(number)
        print()
