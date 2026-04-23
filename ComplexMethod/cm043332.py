def _compute_composite_score(self, metrics, text_len, tag_len, link_text_len):
        """Computes the composite score"""
        if self.min_word_threshold:
            # Get raw text from metrics node - avoid extra processing
            text = metrics["node"].get_text(strip=True)
            word_count = text.count(" ") + 1
            if word_count < self.min_word_threshold:
                return -1.0  # Guaranteed removal
        score = 0.0
        total_weight = 0.0

        if self.metric_config["text_density"]:
            density = text_len / tag_len if tag_len > 0 else 0
            score += self.metric_weights["text_density"] * density
            total_weight += self.metric_weights["text_density"]

        if self.metric_config["link_density"]:
            density = 1 - (link_text_len / text_len if text_len > 0 else 0)
            score += self.metric_weights["link_density"] * density
            total_weight += self.metric_weights["link_density"]

        if self.metric_config["tag_weight"]:
            tag_score = self.tag_weights.get(metrics["tag_name"], 0.5)
            score += self.metric_weights["tag_weight"] * tag_score
            total_weight += self.metric_weights["tag_weight"]

        if self.metric_config["class_id_weight"]:
            class_score = self._compute_class_id_weight(metrics["node"])
            score += self.metric_weights["class_id_weight"] * max(0, class_score)
            total_weight += self.metric_weights["class_id_weight"]

        if self.metric_config["text_length"]:
            score += self.metric_weights["text_length"] * math.log(text_len + 1)
            total_weight += self.metric_weights["text_length"]

        return score / total_weight if total_weight > 0 else 0