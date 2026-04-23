def print_summary_table(data, print_dataframe=False):
    if print_dataframe:
        pd.options.display.max_rows = 1000
        pd.options.display.max_columns = 1000
        pd.options.display.width = 2000
        print(data)
    width = max(map(len, data.columns))
    for col in data.columns:
        try:
            if col in ("dev", "name", "batch_size", "tag"):
                continue
            elif col in ("pct_ops", "pct_time"):
                print(col.ljust(width), f"{data[col].mean():.3%}")
            elif col in ("graphs", "graph_calls", "captured_ops", "total_ops"):
                print(col.ljust(width), f"{data[col].mean():.3f}")
            elif col in ("compilation_latency"):
                print(col.ljust(width), f"mean={data[col].mean():.3f} seconds")
            elif col in ("compression_ratio"):
                print(col.ljust(width), f"mean={data[col].mean():.3f}x")
            elif col in ("accuracy"):
                pass_rate = (data[col] == "pass").mean()
                print(col.ljust(width), f"pass_rate={100 * pass_rate:.2f}%")
            else:
                cdata = data[col]
                print(
                    col.ljust(width),
                    f"gmean={gmean(cdata):.2f}x mean={cdata.mean():.3f}x",
                )
        except Exception:
            pass