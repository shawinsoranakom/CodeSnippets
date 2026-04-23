def equivalent_condition_to_str(self, condition: dict, table_instance=None) -> str | None:
        assert "_id" not in condition
        columns = {}
        if table_instance:
            for n, ty, de, _ in table_instance.show_columns().rows():
                columns[n] = (ty, de)

        def exists(cln):
            nonlocal columns
            assert cln in columns, f"'{cln}' should be in '{columns}'."
            ty, de = columns[cln]
            if ty.lower().find("cha"):
                if not de:
                    de = ""
                return f" {cln}!='{de}' "
            return f"{cln}!={de}"

        cond = list()
        for k, v in condition.items():
            if not isinstance(k, str) or not v:
                continue
            if self.field_keyword(k):
                if isinstance(v, list):
                    inCond = list()
                    for item in v:
                        if isinstance(item, str):
                            item = item.replace("'", "''")
                        inCond.append(f"filter_fulltext('{self.convert_matching_field(k)}', '{item}')")
                    if inCond:
                        strInCond = " or ".join(inCond)
                        strInCond = f"({strInCond})"
                        cond.append(strInCond)
                else:
                    escaped_v = str(v).replace("'", "''")
                    cond.append(f"filter_fulltext('{self.convert_matching_field(k)}', '{escaped_v}')")
            elif isinstance(v, list):
                inCond = list()
                for item in v:
                    if isinstance(item, str):
                        item = item.replace("'", "''")
                        inCond.append(f"'{item}'")
                    else:
                        inCond.append(str(item))
                if inCond:
                    strInCond = ", ".join(inCond)
                    strInCond = f"{k} IN ({strInCond})"
                    cond.append(strInCond)
            elif k == "must_not":
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        if kk == "exists":
                            cond.append("NOT (%s)" % exists(vv))
            elif isinstance(v, str):
                escaped_v = v.replace("'", "''")
                cond.append(f"{k}='{escaped_v}'")
            elif k == "exists":
                cond.append(exists(v))
            else:
                cond.append(f"{k}={str(v)}")
        return " AND ".join(cond) if cond else "1=1"