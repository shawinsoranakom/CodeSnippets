def run():
    parser = argparse.ArgumentParser(
        description="Extracts torchscript IR from log files and, optionally, benchmarks it or outputs the IR"
    )
    parser.add_argument("filename", help="Filename of log file")
    parser.add_argument(
        "--nvfuser", dest="nvfuser", action="store_true", help="benchmark nvfuser"
    )
    parser.add_argument(
        "--no-nvfuser",
        dest="nvfuser",
        action="store_false",
        help="DON'T benchmark nvfuser",
    )
    parser.set_defaults(nvfuser=False)
    parser.add_argument(
        "--nnc-static",
        dest="nnc_static",
        action="store_true",
        help="benchmark nnc static",
    )
    parser.add_argument(
        "--no-nnc-static",
        dest="nnc_static",
        action="store_false",
        help="DON'T benchmark nnc static",
    )
    parser.set_defaults(nnc_static=False)

    parser.add_argument(
        "--nnc-dynamic",
        dest="nnc_dynamic",
        action="store_true",
        help="nnc with dynamic shapes",
    )
    parser.add_argument(
        "--no-nnc-dynamic",
        dest="nnc_dynamic",
        action="store_false",
        help="don't benchmark nnc with dynamic shapes",
    )
    parser.set_defaults(nnc_dynamic=False)

    parser.add_argument(
        "--baseline", dest="baseline", action="store_true", help="benchmark baseline"
    )
    parser.add_argument(
        "--no-baseline",
        dest="baseline",
        action="store_false",
        help="DON'T benchmark baseline",
    )
    parser.set_defaults(baseline=False)

    parser.add_argument(
        "--output", dest="output", action="store_true", help="Output graph IR"
    )
    parser.add_argument(
        "--no-output", dest="output", action="store_false", help="DON'T output graph IR"
    )
    parser.set_defaults(output=False)

    parser.add_argument(
        "--graphs", nargs="+", type=int, help="Run only specified graph indices"
    )

    args = parser.parse_args()
    graphs = extract_ir(args.filename)

    graph_set = args.graphs
    graph_set = graph_set if graph_set else None

    options = []
    if args.baseline:
        options.append(("Baseline no fusion", run_baseline_no_fusion))
    if args.nnc_dynamic:
        options.append(("NNC Dynamic", functools.partial(run_nnc, dynamic=True)))
    if args.nnc_static:
        options.append(("NNC Static", functools.partial(run_nnc, dynamic=False)))
    if args.nvfuser:
        options.append(("NVFuser", run_nvfuser))

    test_runners(graphs, options, graph_set)

    if args.output:
        quoted = []
        for i, ir in enumerate(graphs):
            if graph_set and i not in graph_set:
                continue
            quoted.append('"""' + ir + '"""')
        print("[" + ", ".join(quoted) + "]")