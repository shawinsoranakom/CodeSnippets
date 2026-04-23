def update_view(x, y, d, row=None, col=None):
      if row is None or col is None:
        x = x - self._robot_x
        y = y - self._robot_y
        th = self._robot_ori

        row, col = self._xy_to_rowcol(x, y)
        update_view(x, y, d, row=row, col=col)
        return

      row, row_frac, col, col_frac = int(row), row % 1, int(col), col % 1
      if row_frac < 0:
        row_frac += 1
      if col_frac < 0:
        col_frac += 1

      if valid(row, col):
        self._view[row, col, d] += (
            (min(1., row_frac + 0.5) - max(0., row_frac - 0.5)) *
            (min(1., col_frac + 0.5) - max(0., col_frac - 0.5)))
      if valid(row - 1, col):
        self._view[row - 1, col, d] += (
            (max(0., 0.5 - row_frac)) *
            (min(1., col_frac + 0.5) - max(0., col_frac - 0.5)))
      if valid(row + 1, col):
        self._view[row + 1, col, d] += (
            (max(0., row_frac - 0.5)) *
            (min(1., col_frac + 0.5) - max(0., col_frac - 0.5)))
      if valid(row, col - 1):
        self._view[row, col - 1, d] += (
            (min(1., row_frac + 0.5) - max(0., row_frac - 0.5)) *
            (max(0., 0.5 - col_frac)))
      if valid(row, col + 1):
        self._view[row, col + 1, d] += (
            (min(1., row_frac + 0.5) - max(0., row_frac - 0.5)) *
            (max(0., col_frac - 0.5)))
      if valid(row - 1, col - 1):
        self._view[row - 1, col - 1, d] += (
            (max(0., 0.5 - row_frac)) * max(0., 0.5 - col_frac))
      if valid(row - 1, col + 1):
        self._view[row - 1, col + 1, d] += (
            (max(0., 0.5 - row_frac)) * max(0., col_frac - 0.5))
      if valid(row + 1, col + 1):
        self._view[row + 1, col + 1, d] += (
            (max(0., row_frac - 0.5)) * max(0., col_frac - 0.5))
      if valid(row + 1, col - 1):
        self._view[row + 1, col - 1, d] += (
            (max(0., row_frac - 0.5)) * max(0., 0.5 - col_frac))