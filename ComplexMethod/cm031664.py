def main() -> None:
    from pegen.testutil import print_memstats

    args = argparser.parse_args()
    if "func" not in args:
        argparser.error("Must specify the target language mode ('c' or 'python')")

    t0 = time.time()
    grammar, parser, tokenizer, gen = args.func(args)
    t1 = time.time()

    validate_grammar(grammar)

    if not args.quiet:
        if args.verbose:
            print("Raw Grammar:")
            for line in repr(grammar).splitlines():
                print(" ", line)

        print("Clean Grammar:")
        for line in str(grammar).splitlines():
            print(" ", line)

    if args.verbose:
        print("First Graph:")
        for src, dsts in gen.first_graph.items():
            print(f"  {src} -> {', '.join(dsts)}")
        print("First SCCS:")
        for scc in gen.first_sccs:
            print(" ", scc, end="")
            if len(scc) > 1:
                print(
                    "  # Indirectly left-recursive; leaders:",
                    {name for name in scc if grammar.rules[name].leader},
                )
            else:
                name = next(iter(scc))
                if name in gen.first_graph[name]:
                    print("  # Left-recursive")
                else:
                    print()

    if args.verbose:
        dt = t1 - t0
        diag = tokenizer.diagnose()
        nlines = diag.end[0]
        if diag.type == token.ENDMARKER:
            nlines -= 1
        print(f"Total time: {dt:.3f} sec; {nlines} lines", end="")
        if dt:
            print(f"; {nlines / dt:.0f} lines/sec")
        else:
            print()
        print("Caches sizes:")
        print(f"  token array : {len(tokenizer._tokens):10}")
        print(f"        cache : {len(parser._cache):10}")
        if not print_memstats():
            print("(Can't find psutil; install it for memory stats.)")