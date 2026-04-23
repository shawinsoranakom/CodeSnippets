def read_excel_file(file, category, table):
            """Read the ExcelFile for the sheet name and flatten the table."""
            sheet_name = WpsrTableMap[category][table]
            table_name = read_excel(file, sheet_name, header=None, nrows=1).iloc[0, 1]
            table_name = replace_data_strings(table_name)
            df = read_excel(file, sheet_name, header=[1, 2], nrows=3)
            symbols = df.columns.get_level_values(0).tolist()
            titles = [
                d.replace(".1", "") for d in df.columns.get_level_values(1).tolist()
            ]
            title_map = dict(zip(symbols, titles))
            df = read_excel(file, sheet_name, header=None, skiprows=3)
            df.columns = [d.replace("Sourcekey", "date") for d in symbols]
            df = df.melt(
                id_vars="date",
                value_vars=[d for d in df.columns if d != "date"],
                var_name="symbol",
            ).dropna()
            df = df.reset_index(drop=True)
            df["title"] = df.symbol.map(title_map)
            df["unit"] = df.title.map(lambda x: x.split(" (")[-1].split(")")[0])
            units = [f"({d})" for d in df.unit.unique().tolist()]
            for unit in units:
                df["title"] = df.title.str.replace(unit, "", regex=False).str.strip()
            df["table"] = table_name
            df["order"] = df.groupby("date").cumcount() + 1
            df = df[["date", "table", "symbol", "order", "title", "value", "unit"]]
            df["symbol"] = Categorical(df.symbol, categories=symbols, ordered=True)
            df = df.sort_values(["date", "symbol"])
            df["date"] = df.date.dt.date

            if query.start_date:
                df = df[df.date >= query.start_date]

            if query.end_date:
                df = df[df.date <= query.end_date]

            df = df.reset_index(drop=True)

            if len(df) > 0:
                dfs.append(df)
            else:
                warn(f"No data for table: {table}")