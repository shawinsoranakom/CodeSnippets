def main(import_, options):
    if options.source_file:
        with open(options.source_file, 'r', encoding='utf-8') as source_file:
            prev_results = json.load(source_file)
    else:
        prev_results = {}
    __builtins__.__import__ = import_
    benchmarks = (from_cache, builtin_mod,
                  source_writing_bytecode,
                  source_wo_bytecode, source_using_bytecode,
                  tabnanny_writing_bytecode,
                  tabnanny_wo_bytecode, tabnanny_using_bytecode,
                  decimal_writing_bytecode,
                  decimal_wo_bytecode, decimal_using_bytecode,
                )
    if options.benchmark:
        for b in benchmarks:
            if b.__doc__ == options.benchmark:
                benchmarks = [b]
                break
        else:
            print('Unknown benchmark: {!r}'.format(options.benchmark),
                  file=sys.stderr)
            sys.exit(1)
    seconds = 1
    seconds_plural = 's' if seconds > 1 else ''
    repeat = 3
    header = ('Measuring imports/second over {} second{}, best out of {}\n'
              'Entire benchmark run should take about {} seconds\n'
              'Using {!r} as __import__\n')
    print(header.format(seconds, seconds_plural, repeat,
                        len(benchmarks) * seconds * repeat, __import__))
    new_results = {}
    for benchmark in benchmarks:
        print(benchmark.__doc__, "[", end=' ')
        sys.stdout.flush()
        results = []
        for result in benchmark(seconds=seconds, repeat=repeat):
            results.append(result)
            print(result, end=' ')
            sys.stdout.flush()
        assert not sys.dont_write_bytecode
        print("]", "best is", format(max(results), ',d'))
        new_results[benchmark.__doc__] = results
    if prev_results:
        print('\n\nComparing new vs. old\n')
        for benchmark in benchmarks:
            benchmark_name = benchmark.__doc__
            old_result = max(prev_results[benchmark_name])
            new_result = max(new_results[benchmark_name])
            result = '{:,d} vs. {:,d} ({:%})'.format(new_result,
                                                     old_result,
                                              new_result/old_result)
            print(benchmark_name, ':', result)
    if options.dest_file:
        with open(options.dest_file, 'w', encoding='utf-8') as dest_file:
            json.dump(new_results, dest_file, indent=2)