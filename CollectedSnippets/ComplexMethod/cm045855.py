def _extract_cell_style(self, cell):
        """Extract styles from an openpyxl cell."""
        style = {}
        if cell.font:
            if cell.font.b:
                style["font-weight"] = "bold"
            if cell.font.i:
                style["font-style"] = "italic"
            if cell.font.u:
                style["text-decoration"] = "underline"
            if cell.font.strike:
                style["text-decoration"] = "line-through"
            if (
                cell.font.color
                and hasattr(cell.font.color, "rgb")
                and cell.font.color.rgb
            ):
                # Color might be ARGB "FF000000"
                color = cell.font.color.rgb
                if isinstance(color, str) and len(color) == 8:
                    style["color"] = "#" + color[2:]
                elif isinstance(color, str):
                    style["color"] = "#" + color

        if cell.alignment:
            if cell.alignment.horizontal:
                style["text-align"] = cell.alignment.horizontal
            if cell.alignment.vertical:
                style["vertical-align"] = cell.alignment.vertical

        if cell.fill and cell.fill.patternType == "solid" and cell.fill.fgColor:
            # handle bg color
            color = cell.fill.fgColor.rgb
            if (
                hasattr(cell.fill.fgColor, "type")
                and cell.fill.fgColor.type == "rgb"
                and color
            ):
                if isinstance(color, str) and len(color) == 8:
                    style["background-color"] = "#" + color[2:]
        return style