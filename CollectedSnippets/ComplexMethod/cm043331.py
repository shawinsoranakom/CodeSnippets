def _prune_tree(self, node):
        """
        Prunes the tree starting from the given node.

        Args:
            node (Tag): The node from which the pruning starts.
        """
        if not node or not hasattr(node, "name") or node.name is None:
            return

        text_len = len(node.get_text(strip=True))
        tag_len = len(node.encode_contents().decode("utf-8"))
        link_text_len = sum(
            len(s.strip())
            for s in (a.string for a in node.find_all("a", recursive=False))
            if s
        )

        metrics = {
            "node": node,
            "tag_name": node.name,
            "text_len": text_len,
            "tag_len": tag_len,
            "link_text_len": link_text_len,
        }

        score = self._compute_composite_score(metrics, text_len, tag_len, link_text_len)

        if self.threshold_type == "fixed":
            should_remove = score < self.threshold
        else:  # dynamic
            tag_importance = self.tag_importance.get(node.name, 0.7)
            text_ratio = text_len / tag_len if tag_len > 0 else 0
            link_ratio = link_text_len / text_len if text_len > 0 else 1

            threshold = self.threshold  # base threshold
            if tag_importance > 1:
                threshold *= 0.8
            if text_ratio > 0.4:
                threshold *= 0.9
            if link_ratio > 0.6:
                threshold *= 1.2

            should_remove = score < threshold

        if should_remove:
            node.decompose()
        else:
            children = [child for child in node.children if hasattr(child, "name")]
            for child in children:
                self._prune_tree(child)