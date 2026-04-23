def extract_df(self, metric, testing):
        for iter in itertools.product(self.suites, self.devices, self.dtypes):
            suite, device, dtype = iter
            frames = []
            for compiler in self.compilers:
                output_filename = f"{self.output_dir}/{compiler}_{suite}_{dtype}_{self.mode}_{device}_{testing}.csv"
                df = self.read_csv(output_filename)
                if metric not in df:
                    df.insert(len(df.columns), metric, np.nan)
                df = df[["dev", "name", "batch_size", metric]]
                df.rename(columns={metric: compiler}, inplace=True)
                df["batch_size"] = df["batch_size"].astype(int)
                frames.append(df)

            # Merge the results
            frames = self.clean_batch_sizes(frames)
            if len(self.compilers) == 1:
                df = frames[0]
            else:
                # Merge data frames
                df = pd.merge(frames[0], frames[1], on=["dev", "name", "batch_size"])
                for idx in range(2, len(frames)):
                    df = pd.merge(df, frames[idx], on=["dev", "name", "batch_size"])

            if testing == "performance":
                for compiler in self.compilers:
                    df[compiler] = pd.to_numeric(df[compiler], errors="coerce").fillna(
                        0
                    )

            df_copy = df.copy()
            df_copy = df_copy.sort_values(
                by=list(reversed(self.compilers)), ascending=False
            )
            if "inductor" in self.compilers:
                df_copy = df_copy.sort_values(by="inductor", ascending=False)
            self.untouched_parsed_frames[suite][metric] = df_copy

            if testing == "performance":
                df_accuracy = self.parsed_frames[suite]["accuracy"]
                perf_rows = []
                for model_name in df["name"]:
                    perf_row = df[df["name"] == model_name].copy()
                    acc_row = df_accuracy[df_accuracy["name"] == model_name]
                    for compiler in self.compilers:
                        if not perf_row.empty:
                            if acc_row.empty:
                                perf_row[compiler] = 0.0
                            elif acc_row[compiler].iloc[0] in (
                                "model_fail_to_load",
                                "eager_fail_to_run",
                            ):
                                perf_row = pd.DataFrame()
                            elif acc_row[compiler].iloc[0] not in (
                                "pass",
                                "pass_due_to_skip",
                            ):
                                perf_row[compiler] = 0.0
                    if not perf_row.empty:
                        perf_rows.append(perf_row)
                df = pd.concat(perf_rows)
            df = df.sort_values(by=list(reversed(self.compilers)), ascending=False)

            if "inductor" in self.compilers:
                df = df.sort_values(by="inductor", ascending=False)
            self.parsed_frames[suite][metric] = df