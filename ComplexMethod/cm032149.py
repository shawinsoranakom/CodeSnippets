def get_journal_metrics(self, venue_name: str, venue_info: dict) -> dict:
        """获取期刊指标

        Args:
            venue_name: 期刊名称
            venue_info: 期刊详细信息

        Returns:
            包含期刊指标的字典
        """
        try:
            metrics = {}

            # 1. 首先尝试通过ISSN匹配
            if venue_info and 'issn' in venue_info:
                issn_value = venue_info['issn']
                # 处理ISSN可能是列表的情况
                if isinstance(issn_value, list):
                    # 尝试每个ISSN
                    for issn in issn_value:
                        metrics = self.issn_map.get(issn, {})
                        if metrics:  # 如果找到匹配的指标，就停止搜索
                            break
                else:  # ISSN是字符串的情况
                    metrics = self.issn_map.get(issn_value, {})

            # 2. 如果ISSN匹配失败，尝试通过期刊名称匹配
            if not metrics and venue_name:
                # 标准化期刊名称
                normalized_name = self._normalize_journal_name(venue_name)
                metrics = self.name_map.get(normalized_name, {})

                # 如果完全匹配失败，尝试部分匹配
                # if not metrics:
                #     for db_name, db_metrics in self.name_map.items():
                #         if normalized_name in db_name:
                #             metrics = db_metrics
                #             break

            return metrics

        except Exception as e:
            print(f"获取期刊指标时出错: {str(e)}")
            return {}