def _find_table_bounds(
        self,
        sheet: Worksheet,
        start_row: int,
        start_col: int,
        max_row: int,
        max_col: int,
        gap_tolerance: int,
    ) -> tuple[ExcelTable, set[tuple[int, int]]]:
        """使用洪水填充（BFS）策略确定表格边界。

        该方法通过广度优先搜索（BFS）算法识别 Excel 工作表中连续的非空单元格区域，
        能够准确检测非矩形表格（如 L 形、错位列等），并支持通过间隔容忍度
        连接相邻但不直接相连的单元格。

        算法分两个阶段执行：
        1. 洪水填充阶段：使用 BFS 从给定位置出发，找出所有相连的单元格。
        2. 数据提取阶段：构建矩形边界框并提取单元格数据，正确处理合并单元格。

        参数：
            sheet: 待分析的 Excel 工作表。
            start_row: 洪水填充起始行索引（从0开始）。
            start_col: 洪水填充起始列索引（从0开始）。
            max_row: 工作表中可考虑的最大行索引（从0开始）。
            max_col: 工作表中可考虑的最大列索引（从0开始）。
            gap_tolerance: 允许跨越空白单元格查找邻居的最大间隔。

        返回：
            一个元组，包含：
                - ExcelTable：表示检测到的表格对象，含锚点位置、尺寸和单元格数据。
                - set[tuple[int, int]]：洪水填充期间访问的所有 (行, 列) 元组集合，
                  用于防止重复扫描。

        说明：
            该方法遵循 GAP_TOLERANCE 选项，允许在容忍距离内将被空单元格隔开的
            单元格视为同一表格的一部分。
        """

        # BFS 队列，存储待处理的 (行, 列) 坐标
        queue = collections.deque([(start_row, start_col)])

        # 记录当前表格内已访问的单元格（避免重复加入队列）
        # 调用方维护全局 visited 集合，防止重复启动新表格
        table_cells: set[tuple[int, int]] = set()
        table_cells.add((start_row, start_col))

        # 动态记录当前表格的行列边界
        min_r, max_r = start_row, start_row
        min_c, max_c = start_col, start_col

        def has_content(r, c):
            """检查指定单元格（0-based索引）是否有内容（有值或属于合并区域）。"""
            if r < 0 or c < 0 or r > max_row or c > max_col:
                return False

            # 1. 检查单元格直接值
            cell = sheet.cell(row=r + 1, column=c + 1)
            if cell.value is not None:
                return True

            # 2. 检查是否属于某个合并单元格区域
            for mr in sheet.merged_cells.ranges:
                if cell.coordinate in mr:
                    return True
            return False

        # --- 第一阶段：洪水填充（连通性检测）---
        while queue:
            curr_r, curr_c = queue.popleft()

            # 动态更新表格边界
            min_r = min(min_r, curr_r)
            max_r = max(max_r, curr_r)
            min_c = min(min_c, curr_c)
            max_c = max(max_c, curr_c)

            # 四个方向（上、下、左、右）的邻居检测
            directions = [
                (0, 1),  # 右
                (0, -1),  # 左
                (1, 0),  # 下
                (-1, 0),  # 上
            ]

            for dr, dc in directions:
                # 在容忍距离范围内逐步检查邻居（优先检查最近的）
                for step in range(1, gap_tolerance + 2):
                    nr, nc = curr_r + (dr * step), curr_c + (dc * step)

                    if (nr, nc) in table_cells:
                        break  # 已属于当前表格，不跨越继续查找

                    if has_content(nr, nc):
                        table_cells.add((nr, nc))
                        queue.append((nr, nc))
                        # 在该方向找到连接点，停止扩展间隔
                        break

        # --- 第二阶段：数据提取（语义网格构建）---
        data = []

        # 识别被合并单元格"遮蔽"的单元格（即非合并区域左上角的单元格）
        hidden_merge_cells = set()
        for mr in sheet.merged_cells.ranges:
            mr_min_r, mr_min_c = mr.min_row - 1, mr.min_col - 1
            mr_max_r, mr_max_c = mr.max_row - 1, mr.max_col - 1
            for r in range(mr_min_r, mr_max_r + 1):
                for c in range(mr_min_c, mr_max_c + 1):
                    if r == mr_min_r and c == mr_min_c:
                        continue  # 左上角单元格保留，其余标记为隐藏
                    hidden_merge_cells.add((r, c))

        # 遍历发现区域的边界框（bbox内部的空格作为空单元格保留，维持矩形布局）
        for ri in range(min_r, max_r + 1):
            for rj in range(min_c, max_c + 1):
                # 跳过被合并单元格遮蔽的单元格（非左上角）
                if (ri, rj) in hidden_merge_cells:
                    continue

                # 计算合并跨度（默认为 1x1）
                row_span = 1
                col_span = 1
                for mr in sheet.merged_cells.ranges:
                    if (ri + 1) == mr.min_row and (rj + 1) == mr.min_col:
                        row_span = (mr.max_row - mr.min_row) + 1
                        col_span = (mr.max_col - mr.min_col) + 1
                        break

                data.append(
                    self._build_excel_cell(
                        sheet,
                        ri - min_r,  # 相对于表格起始行的偏移
                        rj - min_c,  # 相对于表格起始列的偏移
                        ri,
                        rj,
                        row_span=row_span,
                        col_span=col_span,
                    )
                )

        # 返回给调用方的 visited_cells 严格为包含数据/合并的单元格，
        # 使主循环不会重复扫描已处理的单元格。
        return (
            ExcelTable(
                anchor=(min_c, min_r),
                num_rows=max_r + 1 - min_r,
                num_cols=max_c + 1 - min_c,
                data=data,
            ),
            table_cells,
        )