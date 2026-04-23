def _collect_table_boxes(page_index, table_x0, table_x1, table_top_cum, table_bottom_cum):
            indices = [
                i
                for i, b in enumerate(self.boxes)
                if (
                    b.get("page_number") == page_index + self.page_from
                    and b.get("layout_type") == "table"
                    and b["x0"] >= table_x0 - 5
                    and b["x1"] <= table_x1 + 5
                    and b["top"] >= table_top_cum - 5
                    and b["bottom"] <= table_bottom_cum + 5
                )
            ]
            original_boxes = [self.boxes[i] for i in indices]
            insert_at = indices[0] if indices else len(self.boxes)
            for i in reversed(indices):
                self.boxes.pop(i)
            return original_boxes, insert_at