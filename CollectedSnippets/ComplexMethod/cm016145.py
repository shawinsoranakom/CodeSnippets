def generate_diff(self, last2, filename, caption):
        df_cur, df_prev = (pd.read_csv(os.path.join(path, filename)) for path in last2)
        df_merge = df_cur.merge(df_prev, on="Compiler", suffixes=("_cur", "_prev"))
        data = {col: [] for col in ("compiler", "suite", "prev_value", "cur_value")}
        for _, row in df_merge.iterrows():
            if row["Compiler"] in self.args.flag_compilers:
                for suite in self.args.suites:
                    if suite + "_prev" not in row or suite + "_cur" not in row:
                        continue
                    data["compiler"].append(row["Compiler"])
                    data["suite"].append(suite)
                    data["prev_value"].append(row[suite + "_prev"])
                    data["cur_value"].append(row[suite + "_cur"])

        df = pd.DataFrame(data)
        tabform = tabulate(df, headers="keys", tablefmt="pretty", showindex="never")
        str_io = io.StringIO()
        str_io.write("\n")
        str_io.write(f"{caption}\n")
        str_io.write("~~~\n")
        str_io.write(f"{tabform}\n")
        str_io.write("~~~\n")
        return str_io.getvalue()