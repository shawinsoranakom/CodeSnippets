def get_highlight(self, res: tuple[pd.DataFrame, int] | pd.DataFrame, keywords: list[str], field_name: str):
        # Extract DataFrame from result
        if isinstance(res, tuple):
            df, _ = res
        else:
            df = res

        if df.empty or field_name not in df.columns:
            return {}

        ans = {}
        num_rows = len(res)
        column_id = res["id"]
        if field_name not in res:
            if field_name == "content_with_weight" and "content" in res:
                field_name = "content"
            else:
                return {}
        for i in range(num_rows):
            id = column_id[i]
            txt = res[field_name][i]
            if re.search(r"<em>[^<>]+</em>", txt, flags=re.IGNORECASE | re.MULTILINE):
                ans[id] = txt
                continue
            txt = re.sub(r"[\r\n]", " ", txt, flags=re.IGNORECASE | re.MULTILINE)
            txt_list = []
            for t in re.split(r"[.?!;\n]", txt):
                if is_english([t]):
                    for w in keywords:
                        t = re.sub(
                            r"(^|[ .?/'\"\(\)!,:;-])(%s)([ .?/'\"\(\)!,:;-])" % re.escape(w),
                            r"\1<em>\2</em>\3",
                            t,
                            flags=re.IGNORECASE | re.MULTILINE,
                        )
                else:
                    for w in sorted(keywords, key=len, reverse=True):
                        t = re.sub(
                            re.escape(w),
                            f"<em>{w}</em>",
                            t,
                            flags=re.IGNORECASE | re.MULTILINE,
                        )
                if not re.search(r"<em>[^<>]+</em>", t, flags=re.IGNORECASE | re.MULTILINE):
                    continue
                txt_list.append(t)
            if txt_list:
                ans[id] = "...".join(txt_list)
            else:
                ans[id] = txt
        return ans