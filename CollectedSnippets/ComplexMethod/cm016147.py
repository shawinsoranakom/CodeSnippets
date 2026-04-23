def diff(self):
        log_infos = self.find_last_k()

        for metric in ["geomean", "passrate", "comp_time", "memory"]:
            fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))
            for idx, suite in enumerate(self.suites):
                dfs = []
                for log_info in log_infos:
                    dir_path = os.path.join(
                        self.args.dashboard_archive_path, log_info.dir_path
                    )
                    if not os.path.exists(dir_path):
                        raise AssertionError(f"directory not found: {dir_path}")
                    gmean_filename = os.path.join(dir_path, f"{metric}.csv")
                    if not os.path.exists(gmean_filename):
                        continue
                    df = pd.read_csv(gmean_filename)
                    if suite not in df:
                        continue
                    if metric == "geomean" or metric == "memory":
                        df[suite] = df[suite].str.replace("x", "").astype(float)
                    elif metric == "passrate":
                        df[suite] = df[suite].str.split("%").str[0].astype(float)
                    df.insert(0, "day", get_date(log_info))
                    df = df.pivot(index="day", columns="Compiler", values=suite)

                    # Interim stage when both inductor_cudagraphs and inductor exist
                    df = df.rename(columns={"inductor_cudagraphs": "inductor"})
                    for col_name in df.columns:
                        if col_name not in self.args.compilers:
                            df = df.drop(columns=[col_name])
                    dfs.append(df)

                df = pd.concat(dfs)
                df = df.interpolate(method="linear")
                ax = df.plot(
                    ax=axes[idx],
                    kind="line",
                    ylabel=metric,
                    xlabel="Date",
                    grid=True,
                    ylim=0 if metric == "passrate" else 0.8,
                    title=suite,
                    style=".-",
                    legend=False,
                )
                ax.legend(loc="lower right", ncol=2)

            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{metric}_over_time.png"))

        self.generate_comment()