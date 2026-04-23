def main() -> None:
    """
    Main function for the profile analysis script.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--diff",
        nargs=5,
        metavar=(
            "input_file1",
            "name1",
            "input_file2",
            "name2",
            "dtype",
        ),
        help="Two json traces to compare with, specified as <file1> <name1> <file2> <name2> <dtype>",
    )
    parser.add_argument(
        "--name_limit",
        type=int,
        help="the maximum name size in the final report",
    )
    parser.add_argument(
        "--augment_trace",
        "-a",
        nargs=3,
        metavar=("input_file", "output_file", "dtype"),
        help="Augment a trace with inductor meta information. Provide input and output file paths.",
    )
    parser.add_argument(
        "--analysis",
        nargs=2,
        metavar=("input_file", "dtype"),
        help="Run analysis on a single trace, specified as <file> <dtype>",
    )
    parser.add_argument(
        "--combine",
        nargs="+",
        metavar=("input_files", "output_file"),
        help="Combine multiple profiles into a single profile by merging trace events. Specify as <input_file1> \
<input_file2> [input_file3 ...] <output_file>. The last argument is the output file, all preceding arguments are \
input files to combine.",
    )
    args = parser.parse_args()

    if args.diff:
        p1 = JsonProfile(args.diff[0], args.diff[1], dtype=args.diff[4])
        p1.augment_trace()
        p2 = JsonProfile(args.diff[2], args.diff[3], dtype=args.diff[4])
        p2.augment_trace()
        if args.name_limit:
            print(p1.report(p2, name_limit=args.name_limit))
        else:
            print(p1.report(p2))
    if args.analysis:
        p1 = JsonProfile(
            args.analysis[0],
            dtype=args.analysis[1],
        )
        p1.augment_trace()
        if args.name_limit:
            print(p1.report(name_limit=args.name_limit))
        else:
            print(p1.report())
    if args.augment_trace:
        p = JsonProfile(args.augment_trace[0], dtype=args.augment_trace[2])
        p.augment_trace()
        p.dump(args.augment_trace[1])
    if args.combine:
        input_files = args.combine[:-1]  # All arguments except the last one
        output_file = args.combine[-1]  # Last argument is the output file

        if len(input_files) < 2:
            print("Error: At least 2 input files are required for combining")
            return

        # Load the first profile
        combined = JsonProfile(input_files[0], dtype=None)

        # Iteratively combine with all other profiles
        for input_file in input_files[1:]:
            profile = JsonProfile(input_file, dtype=None)
            combined = combined.combine_with(profile)

        combined.dump(output_file)
        print(f"Successfully combined {', '.join(input_files)} into {output_file}")