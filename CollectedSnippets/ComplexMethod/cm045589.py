def _format_types(x):
        if pd.isna(x):
            return None
        if isinstance(x, api.Pointer):
            s = str(x)
            if len(s) > 8 and short_pointers:
                s = s[:8] + "..."
            return s
        if isinstance(x, pd.Timestamp):
            return x.strftime("%Y-%m-%d %H:%M:%S%z")
        if isinstance(x, pw.Json):
            s = str(x)
            if len(s) > 64:
                s = s[:64] + " ..."
            return s
        return x