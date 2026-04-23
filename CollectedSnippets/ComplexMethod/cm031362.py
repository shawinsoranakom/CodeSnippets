def __plan_refresh(
        self,
        rendered_screen: RenderedScreen,
        c_xy: tuple[int, int],
    ) -> UnixRefreshPlan:
        cx, cy = c_xy
        height = self.height
        old_offset = offset = self.__offset
        prev_composed = self._rendered_screen.composed_lines
        previous_lines = list(prev_composed)
        next_lines = list(rendered_screen.composed_lines)
        line_count = len(next_lines)

        grow_lines = 0
        if not self.__gone_tall:
            grow_lines = max(
                min(line_count, height) - len(prev_composed),
                0,
            )
            previous_lines.extend([EMPTY_RENDER_LINE] * grow_lines)
        elif len(previous_lines) < line_count:
            previous_lines.extend([EMPTY_RENDER_LINE] * (line_count - len(previous_lines)))

        use_tall_mode = self.__gone_tall or line_count > height

        # we make sure the cursor is on the screen, and that we're
        # using all of the screen if we can
        if cy < offset:
            offset = cy
        elif cy >= offset + height:
            offset = cy - height + 1
        elif offset > 0 and line_count < offset + height:
            offset = max(line_count - height, 0)
            next_lines.append(EMPTY_RENDER_LINE)

        oldscr = previous_lines[old_offset : old_offset + height]
        newscr = next_lines[offset : offset + height]

        reverse_scroll = 0
        forward_scroll = 0
        if old_offset > offset and self._ri:
            reverse_scroll = old_offset - offset
            for _ in range(reverse_scroll):
                if oldscr:
                    oldscr.pop(-1)
                oldscr.insert(0, EMPTY_RENDER_LINE)
        elif old_offset < offset and self._ind:
            forward_scroll = offset - old_offset
            for _ in range(forward_scroll):
                if oldscr:
                    oldscr.pop(0)
                oldscr.append(EMPTY_RENDER_LINE)

        line_updates: list[LineUpdate] = []
        px, _ = self.posxy
        for y, oldline, newline in zip(range(offset, offset + height), oldscr, newscr):
            update = self.__plan_changed_line(y, oldline, newline, px)
            if update is not None:
                line_updates.append(update)

        cleared_lines = tuple(range(offset + len(newscr), offset + len(oldscr)))
        console_rendered_screen = RenderedScreen(tuple(next_lines), c_xy)
        trace(
            "unix.refresh plan grow={grow} tall={tall} offset={offset} "
            "reverse_scroll={reverse_scroll} forward_scroll={forward_scroll} "
            "updates={updates} clears={clears}",
            grow=grow_lines,
            tall=use_tall_mode,
            offset=offset,
            reverse_scroll=reverse_scroll,
            forward_scroll=forward_scroll,
            updates=len(line_updates),
            clears=len(cleared_lines),
        )
        return UnixRefreshPlan(
            grow_lines=grow_lines,
            use_tall_mode=use_tall_mode,
            offset=offset,
            reverse_scroll=reverse_scroll,
            forward_scroll=forward_scroll,
            line_updates=tuple(line_updates),
            cleared_lines=cleared_lines,
            rendered_screen=console_rendered_screen,
            cursor=(cx, cy),
        )