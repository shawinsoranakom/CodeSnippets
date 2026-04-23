def method(self, other_args: list[str], translator=translator):
            """Call the translator."""
            parser = translator.parser

            if ns_parser := self.parse_known_args_and_warn(
                parser=parser,
                other_args=other_args,
                export_allowed="raw_data_and_figures",
            ):
                try:
                    ns_parser = self._intersect_data_processing_commands(ns_parser)
                    export = hasattr(ns_parser, "export") and ns_parser.export
                    store_obbject = (
                        hasattr(ns_parser, "register_obbject")
                        and ns_parser.register_obbject
                    )

                    obbject = translator.execute_func(parsed_args=ns_parser)
                    df: pd.DataFrame = pd.DataFrame()
                    fig: OpenBBFigure | None = None
                    title = f"{self.PATH}{translator.func.__name__}"

                    if obbject:
                        if isinstance(obbject, list):
                            obbject = OBBject(results=obbject)

                        if isinstance(obbject, OBBject):
                            if (
                                session.max_obbjects_exceeded()
                                and obbject.results
                                and store_obbject
                            ):
                                session.obbject_registry.remove()
                                session.console.print(
                                    "[yellow]Maximum number of OBBjects reached. The oldest entry was removed.[yellow]"
                                )

                            # use the obbject to store the command so we can display it later on results
                            obbject.extra["command"] = f"{title} {' '.join(other_args)}"
                            # if there is a registry key in the parser, store to the obbject
                            if (
                                hasattr(ns_parser, "register_key")
                                and ns_parser.register_key
                            ):
                                if (
                                    ns_parser.register_key
                                    not in session.obbject_registry.obbject_keys
                                ):
                                    obbject.extra["register_key"] = str(
                                        ns_parser.register_key
                                    )
                                else:
                                    session.console.print(
                                        f"[yellow]Key `{ns_parser.register_key}` already exists in the registry."
                                        "The `OBBject` was kept without the key.[/yellow]"
                                    )

                            if store_obbject:
                                # store the obbject in the registry
                                register_result = session.obbject_registry.register(
                                    obbject
                                )

                                # we need to force to re-link so that the new obbject
                                # is immediately available for data processing commands
                                self._link_obbject_to_data_processing_commands()
                                # also update the completer
                                self.update_completer(self.choices_default)

                                if (
                                    session.settings.SHOW_MSG_OBBJECT_REGISTRY
                                    and register_result
                                ):
                                    session.console.print(
                                        "Added `OBBject` to cached results."
                                    )

                            # making the dataframe available either for printing or exporting
                            df = obbject.to_dataframe()

                            if hasattr(ns_parser, "chart") and ns_parser.chart:
                                fig = obbject.chart.fig if obbject.chart else None
                                if not export:
                                    obbject.show()
                            elif session.settings.USE_INTERACTIVE_DF and not export:
                                obbject.charting.table()  # type: ignore[attr-defined]
                            else:
                                if isinstance(df.columns, pd.RangeIndex):
                                    df.columns = [str(i) for i in df.columns]

                                print_rich_table(
                                    df=df, show_index=True, title=title, export=export
                                )

                        elif isinstance(obbject, dict):
                            df = pd.DataFrame.from_dict(obbject, orient="columns")
                            print_rich_table(
                                df=df, show_index=True, title=title, export=export
                            )

                        elif not isinstance(obbject, OBBject):
                            session.console.print(obbject)

                    if export and not df.empty:
                        sheet_name = getattr(ns_parser, "sheet_name", None)
                        if sheet_name and isinstance(sheet_name, list):
                            sheet_name = sheet_name[0]

                        export_data(
                            export_type=",".join(ns_parser.export),
                            dir_path=os.path.dirname(os.path.abspath(__file__)),
                            func_name=translator.func.__name__,
                            df=df,
                            sheet_name=sheet_name,
                            figure=fig,
                        )
                    elif export and df.empty:
                        session.console.print("[yellow]No data to export.[/yellow]")

                except Exception as e:
                    session.console.print(f"[red]{e}[/]\n")
                    return