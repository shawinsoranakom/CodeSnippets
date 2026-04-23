def __iter__(self):
        for entry in self.source:

            # determine <module>.<imd_name> from res_id
            if entry["res_id"] and entry["res_id"].isnumeric():
                # res_id is an id or line number
                entry["res_id"] = int(entry["res_id"])
            elif not entry.get("imd_name"):
                # res_id is an external id and must follow <module>.<name>
                entry["module"], entry["imd_name"] = entry["res_id"].split(".")
                entry["res_id"] = None
            if entry["type"] == "model" or entry["type"] == "model_terms":
                entry["imd_model"] = entry["name"].partition(',')[0]

            if entry["type"] == "code":
                if entry["src"] == self.prev_code_src:
                    # skip entry due to unicity constrain on code translations
                    continue
                self.prev_code_src = entry["src"]

            yield entry