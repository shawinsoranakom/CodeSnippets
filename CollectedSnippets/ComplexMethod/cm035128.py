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
                # print('before')
                # print(node1.content, node2.content)
                # print('after')
                node1_content = node1.content
                node2_content = node2.content
                if len(node1_content) < 3:
                    node1_content = ["####"]
                if len(node2_content) < 3:
                    node2_content = ["####"]
                return Levenshtein.normalized_distance(node1_content, node2_content)
        return 0.0