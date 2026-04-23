def get_highlight(self, res, keywords: list[str], field_name: str):
        ans = {}
        for d in res["hits"]["hits"]:
            highlights = d.get("highlight")
            if not highlights:
                continue
            txt = "...".join([a for a in list(highlights.items())[0][1]])
            if not is_english(txt.split()):
                ans[d["_id"]] = txt
                continue

            txt = d["_source"][field_name]
            txt = re.sub(r"[\r\n]", " ", txt, flags=re.IGNORECASE | re.MULTILINE)
            txt_list = []
            for t in re.split(r"[.?!;\n]", txt):
                for w in keywords:
                    t = re.sub(r"(^|[ .?/'\"\(\)!,:;-])(%s)([ .?/'\"\(\)!,:;-])" % re.escape(w), r"\1<em>\2</em>\3", t,
                               flags=re.IGNORECASE | re.MULTILINE)
                if not re.search(r"<em>[^<>]+</em>", t, flags=re.IGNORECASE | re.MULTILINE):
                    continue
                txt_list.append(t)
            ans[d["_id"]] = "...".join(txt_list) if txt_list else "...".join([a for a in list(highlights.items())[0][1]])

        return ans