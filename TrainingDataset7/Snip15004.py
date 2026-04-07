def visit_section(self, node):
        old_ids = node.get("ids", [])
        node["ids"] = ["s-" + i for i in old_ids]
        node["ids"].extend(old_ids)
        super().visit_section(node)
        node["ids"] = old_ids