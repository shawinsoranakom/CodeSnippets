def _merge_excels(self):
        """Merge multiple Excel files/sheets into one."""
        all_dfs = []

        for file_ref in (self._param.input_files or []):
            if self.check_if_canceled("ExcelProcessor merging"):
                return

            value = self._canvas.get_variable_value(file_ref)
            self.set_input_value(file_ref, str(value)[:200] if value else "")

            if value is None:
                continue

            content, filename = self._get_file_content(file_ref)
            if content is None:
                continue

            dfs = self._parse_excel_to_dataframes(content, filename)
            all_dfs.extend(dfs.values())

        if not all_dfs:
            self.set_output("data", {})
            self.set_output("summary", "No data to merge")
            return

        # Merge strategy
        if self._param.merge_strategy == "concat":
            merged_df = pd.concat(all_dfs, ignore_index=True)
        elif self._param.merge_strategy == "join" and self._param.join_on:
            # Join on specified column
            merged_df = all_dfs[0]
            for df in all_dfs[1:]:
                merged_df = merged_df.merge(df, on=self._param.join_on, how="outer")
        else:
            merged_df = pd.concat(all_dfs, ignore_index=True)

        self.set_output("data", {"merged": merged_df.to_dict(orient="records")})
        self.set_output("summary", f"Merged {len(all_dfs)} sources into {len(merged_df)} rows, {len(merged_df.columns)} columns")
        self.set_output("markdown", merged_df.head(20).to_markdown(index=False))