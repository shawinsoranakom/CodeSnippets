def _get_year_as_int(self, paper) -> int:
        """统一获取论文年份为整数格式

        Args:
            paper: 论文对象或直接是年份值

        Returns:
            整数格式的年份，如果无法转换则返回0
        """
        try:
            # 如果输入直接是年份而不是论文对象
            if isinstance(paper, int):
                return paper
            elif isinstance(paper, str):
                try:
                    return int(paper)
                except ValueError:
                    import re
                    year_match = re.search(r'\d{4}', paper)
                    if year_match:
                        return int(year_match.group())
                    return 0
            elif isinstance(paper, float):
                return int(paper)

            # 处理论文对象
            year = getattr(paper, 'year', None)
            if year is None:
                return 0

            # 如果是字符串，尝试转换为整数
            if isinstance(year, str):
                # 首先尝试直接转换整个字符串
                try:
                    return int(year)
                except ValueError:
                    # 如果直接转换失败，尝试提取第一个数字序列
                    import re
                    year_match = re.search(r'\d{4}', year)
                    if year_match:
                        return int(year_match.group())
                    return 0
            # 如果是浮点数，转换为整数
            elif isinstance(year, float):
                return int(year)
            # 如果已经是整数，直接返回
            elif isinstance(year, int):
                return year
            return 0
        except (ValueError, TypeError):
            return 0