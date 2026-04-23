def _format_text(
        self,
        service,
        document_id: str,
        start_index: int,
        end_index: int,
        bold: bool,
        italic: bool,
        underline: bool,
        font_size: int,
        foreground_color: str,
    ) -> dict:
        text_style: dict[str, Any] = {}
        fields = []

        if bold:
            text_style["bold"] = True
            fields.append("bold")
        if italic:
            text_style["italic"] = True
            fields.append("italic")
        if underline:
            text_style["underline"] = True
            fields.append("underline")
        if font_size > 0:
            text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
            fields.append("fontSize")
        if foreground_color:
            rgb = _parse_hex_color_to_rgb_floats(foreground_color)
            if rgb is None:
                if not fields:
                    return {
                        "success": False,
                        "message": (
                            f"Invalid foreground_color: {foreground_color!r}. "
                            "Expected hex like #RGB or #RRGGBB."
                        ),
                    }
                # Ignore invalid color, but still apply other formatting.
                # This avoids failing the whole operation due to a single bad value.
                warning = (
                    f"Ignored invalid foreground_color: {foreground_color!r}. "
                    "Expected hex like #RGB or #RRGGBB."
                )
            else:
                r, g, b = rgb
                text_style["foregroundColor"] = {
                    "color": {"rgbColor": {"red": r, "green": g, "blue": b}}
                }
                fields.append("foregroundColor")
                warning = None
        else:
            warning = None

        if not fields:
            return {"success": True, "message": "No formatting options specified"}

        requests = [
            {
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "textStyle": text_style,
                    "fields": ",".join(fields),
                }
            }
        ]

        service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

        if warning:
            return {"success": True, "warning": warning}
        return {"success": True}