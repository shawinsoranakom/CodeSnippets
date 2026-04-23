def _render_line(
        self,
        prefix: str,
        fragments: tuple[ContentFragment, ...],
        suffix: str = "",
    ) -> RenderLine:
        cells: list[RenderCell] = []
        if prefix:
            cache_key = (prefix, self.can_colorize)
            cached = self._prompt_cell_cache.get(cache_key)
            if cached is None:
                prompt_cells = RenderLine.from_rendered_text(prefix).cells
                if self.can_colorize and prompt_cells and not ANSI_ESCAPE_SEQUENCE.search(prefix):
                    prompt_style = StyleRef.from_tag("prompt", THEME()["prompt"])
                    prompt_cells = tuple(
                        RenderCell(
                            cell.text,
                            cell.width,
                            style=prompt_style if cell.text else cell.style,
                            controls=cell.controls,
                        )
                        for cell in prompt_cells
                    )
                self._prompt_cell_cache[cache_key] = prompt_cells
                cached = prompt_cells
            cells.extend(cached)
        cells.extend(
            RenderCell(fragment.text, fragment.width, style=fragment.style)
            for fragment in fragments
        )
        if suffix:
            cells.extend(RenderLine.from_rendered_text(suffix).cells)
        return RenderLine.from_cells(cells)