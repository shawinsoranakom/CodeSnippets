def generate_comment(self):
        title = "## Recent Regressions ##\n"
        body = (
            "For each relevant compiler, we compare the most recent 2 reports "
            "(that actually run the compiler) to find previously unflagged "
            "models that are now flagged as problematic (according to the "
            "'Warnings' section).\n\n"
        )
        dtype = self.args.dtypes[0]
        device = self.args.devices[0]
        for suite in self.args.suites:
            body += f"### Regressions for {suite} ###\n"
            last2 = {}

            for compiler in self.args.flag_compilers:
                filenames = [
                    generate_csv_name(
                        self.args, dtype, suite, device, compiler, testing
                    )
                    for testing in ["performance", "accuracy"]
                ]
                compiler_last2 = find_last_2_with_filenames(
                    self.lookup_file, self.args.dashboard_archive_path, dtype, filenames
                )
                if compiler_last2 is not None:
                    last2[compiler] = [
                        ParsePerformanceLogs(
                            [suite],
                            [device],
                            [dtype],
                            [compiler],
                            [compiler],
                            get_mode(self.args),
                            output_dir,
                        )
                        for output_dir in compiler_last2
                    ]
                    for state, path in zip(("Current", "Previous"), compiler_last2):
                        body += (
                            f"{state} report name (compiler: {compiler}, "
                            f"suite: {suite}): {path}\n\n"
                        )

            regressions_present = False
            for metric in [
                "accuracy",
                "speedup",
                "compilation_latency",
                "compression_ratio",
            ]:
                dfs = []
                for compiler in self.args.flag_compilers:
                    if last2[compiler] is None:
                        continue

                    df_cur, df_prev = (
                        last2[compiler][i].untouched_parsed_frames[suite][metric]
                        for i in (0, 1)
                    )
                    df_merge = df_cur.merge(
                        df_prev, on="name", suffixes=("_cur", "_prev")
                    )
                    flag_fn = FLAG_FNS[metric]
                    flag = np.logical_and(
                        df_merge[compiler + "_prev"].apply(
                            lambda x: not pd.isna(x) and not flag_fn(x)
                        ),
                        df_merge[compiler + "_cur"].apply(
                            lambda x: not pd.isna(x) and flag_fn(x)
                        ),
                    )
                    df_bad = df_merge[flag]
                    dfs.append(
                        pd.DataFrame(
                            data={
                                "compiler": compiler,
                                "name": df_bad["name"],
                                "prev_status": df_bad[compiler + "_prev"],
                                "cur_status": df_bad[compiler + "_cur"],
                            }
                        )
                    )

                if not dfs:
                    continue
                df = pd.concat(dfs, axis=0)
                if df.empty:
                    continue
                regressions_present = True
                tabform = tabulate(
                    df, headers="keys", tablefmt="pretty", showindex="never"
                )
                str_io = io.StringIO()
                str_io.write("\n")
                str_io.write(f"{get_metric_title(metric)} regressions\n")
                str_io.write("~~~\n")
                str_io.write(f"{tabform}\n")
                str_io.write("~~~\n")
                body += str_io.getvalue()

            if not regressions_present:
                body += "No regressions found.\n"

        comment = generate_dropdown_comment(title, body)

        with open(f"{self.args.output_dir}/gh_metric_regression.txt", "w") as gh_fh:
            gh_fh.write(comment)