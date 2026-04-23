def _parse_excel_to_dataframes(self, content: bytes, filename: str) -> dict[str, pd.DataFrame]:
        """Parse Excel content into a dictionary of DataFrames (one per sheet)."""
        try:
            excel_file = BytesIO(content)

            if filename.lower().endswith(".csv"):
                df = pd.read_csv(excel_file)
                return {"Sheet1": df}
            else:
                # Read all sheets
                xlsx = pd.ExcelFile(excel_file, engine='openpyxl')
                sheet_selection = self._param.sheet_selection

                if sheet_selection == "all":
                    sheets_to_read = xlsx.sheet_names
                elif sheet_selection == "first":
                    sheets_to_read = [xlsx.sheet_names[0]] if xlsx.sheet_names else []
                else:
                    # Comma-separated sheet names
                    requested = [s.strip() for s in sheet_selection.split(",")]
                    sheets_to_read = [s for s in requested if s in xlsx.sheet_names]

                dfs = {}
                for sheet in sheets_to_read:
                    dfs[sheet] = pd.read_excel(xlsx, sheet_name=sheet)
                return dfs

        except Exception as e:
            logging.error(f"Error parsing Excel file {filename}: {e}")
            return {}