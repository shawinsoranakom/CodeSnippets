def __apply_refresh_plan(self, plan: UnixRefreshPlan) -> None:
        cx, cy = plan.cursor
        trace(
            "unix.refresh apply cursor={cursor} updates={updates} clears={clears}",
            cursor=plan.cursor,
            updates=len(plan.line_updates),
            clears=len(plan.cleared_lines),
        )
        visual_style = self.begin_redraw_visualization()
        screen_line_count = len(self._rendered_screen.composed_lines)

        for _ in range(plan.grow_lines):
            self.__hide_cursor()
            if screen_line_count:
                self.__move(0, screen_line_count - 1)
                self.__write("\n")
            self.posxy = 0, screen_line_count
            screen_line_count += 1

        if plan.use_tall_mode and not self.__gone_tall:
            self.__gone_tall = True
            self.__move = self.__move_tall

        old_offset = self.__offset
        if plan.reverse_scroll:
            self.__hide_cursor()
            self.__write_code(self._cup, 0, 0)
            self.posxy = 0, old_offset
            for _ in range(plan.reverse_scroll):
                self.__write_code(self._ri)
        elif plan.forward_scroll:
            self.__hide_cursor()
            self.__write_code(self._cup, self.height - 1, 0)
            self.posxy = 0, old_offset + self.height - 1
            for _ in range(plan.forward_scroll):
                self.__write_code(self._ind)

        self.__offset = plan.offset

        for update in plan.line_updates:
            self.__apply_line_update(update, visual_style)

        for y in plan.cleared_lines:
            self.__hide_cursor()
            self.__move(0, y)
            self.posxy = 0, y
            self.__write_code(self._el)

        self.__show_cursor()
        self.move_cursor(cx, cy)
        self.flushoutput()
        self.sync_rendered_screen(plan.rendered_screen, self.posxy)