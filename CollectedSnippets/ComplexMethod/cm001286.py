async def main():
    parser = argparse.ArgumentParser(
        description="Analyze benchmark failures across prompt strategies"
    )
    parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Disable LLM-powered analysis",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        help="Focus on a specific strategy",
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Compare a specific test across strategies",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--markdown",
        type=str,
        nargs="?",
        const="failure_analysis.md",
        help="Export to markdown (optionally specify output file)",
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        default=None,
        help="Path to reports directory",
    )

    args = parser.parse_args()

    # Find reports directory
    if args.reports_dir:
        reports_dir = Path(args.reports_dir)
    else:
        # Try to find it relative to this script
        script_dir = Path(__file__).parent
        reports_dir = script_dir / "reports"
        if not reports_dir.exists():
            reports_dir = Path.cwd() / "agbenchmark_config" / "reports"

    if not reports_dir.exists():
        print(f"Reports directory not found: {reports_dir}")
        sys.exit(1)

    analyzer = FailureAnalyzer(reports_dir, use_llm=not args.no_analysis)
    analyzer.analyze_all()

    if not analyzer.strategies:
        print("No strategy reports found.")
        sys.exit(1)

    if args.interactive:
        analyzer.interactive_mode()
    elif args.test:
        analyzer.compare_test(args.test)
    elif args.strategy:
        analyzer.print_failed_tests(args.strategy)
    else:
        analyzer.print_summary()
        analyzer.print_pattern_analysis()
        analyzer.print_failed_tests()

    if args.markdown:
        output_path = Path(args.markdown)
        analyzer.export_markdown(output_path)