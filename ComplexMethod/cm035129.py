def rename(self, node1, node2):
        """Compares attributes of trees"""
        if (
            (node1.tag != node2.tag)
            or (node1.colspan != node2.colspan)
            or (node1.rowspan != node2.rowspan)
        ):
            return 1.0
        if node1.tag == "td":
            if node1.content or node2.content:
                node1_content = node1.content
                node2_content = node2.content
                while " " in node1_content:
                    print(node1_content.index(" "))
                    node1_content.pop(node1_content.index(" "))
                while " " in node2_content:
                    print(node2_content.index(" "))
                    node2_content.pop(node2_content.index(" "))
                return Levenshtein.normalized_distance(node1_content, node2_content)
        return 0.0