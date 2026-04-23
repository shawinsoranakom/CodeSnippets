def call_results(self, other_args: list[str]):
        """Process results command."""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="results",
            description="Process results command. This command displays a registry of "
            "'OBBjects' where all execution results are stored. "
            "It is organized as a stack, with the most recent result at index 0.",
        )
        parser.add_argument("--index", dest="index", help="Index of the result.")
        parser.add_argument("--key", dest="key", help="Key of the result.")
        parser.add_argument(
            "--chart", action="store_true", dest="chart", help="Display chart."
        )
        parser.add_argument(
            "--export",
            default="",
            type=check_file_type_saved(["csv", "json", "xlsx", "png", "jpg"]),
            dest="export",
            help="Export raw data into csv, json, xlsx and figure into png or jpg.",
            nargs="+",
        )
        parser.add_argument(
            "--sheet-name",
            dest="sheet_name",
            default=None,
            nargs="+",
            help="Name of excel sheet to save data to. Only valid for .xlsx files.",
        )

        ns_parser, unknown_args = self.parse_simple_args(
            parser, other_args, unknown_args=True
        )

        if ns_parser:
            kwargs = parse_unknown_args_to_dict(unknown_args)
            if not ns_parser.index and not ns_parser.key:
                results = session.obbject_registry.all
                if results:
                    df = pd.DataFrame.from_dict(results, orient="index")
                    print_rich_table(
                        df,
                        show_index=True,
                        index_name="stack index",
                        title="OBBject Results",
                    )
                else:
                    session.console.print("[info]No results found.[/info]")
            elif ns_parser.index:
                try:
                    index = int(ns_parser.index)
                    obbject = session.obbject_registry.get(index)
                    if obbject:
                        handle_obbject_display(
                            obbject=obbject,
                            chart=ns_parser.chart,
                            export=ns_parser.export,
                            sheet_name=ns_parser.sheet_name,
                            **kwargs,
                        )
                    else:
                        session.console.print(
                            f"[info]No result found at index {index}.[/info]"
                        )
                except ValueError:
                    session.console.print(
                        f"[red]Index must be an integer, not '{ns_parser.index}'.[/red]"
                    )
            elif ns_parser.key:
                obbject = session.obbject_registry.get(ns_parser.key)
                if obbject:
                    handle_obbject_display(
                        obbject=obbject,
                        chart=ns_parser.chart,
                        export=ns_parser.export,
                        sheet_name=ns_parser.sheet_name,
                        **kwargs,
                    )
                else:
                    session.console.print(
                        f"[info]No result found with key '{ns_parser.key}'.[/info]"
                    )