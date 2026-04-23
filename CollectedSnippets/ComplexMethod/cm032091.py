def _process_chunk(self, chunk: pd.DataFrame, columns: Optional[List[str]] = None, sheet_name: str = '') -> str:
        """处理数据块，新增sheet_name参数"""
        try:
            if columns:
                chunk = chunk[columns]

            if self.config.preserve_format:
                formatted_chunk = chunk.applymap(self._format_value)
                rows = []

                # 添加工作表名称作为标题
                if sheet_name:
                    rows.append(f"[Sheet: {sheet_name}]")

                # 添加表头
                headers = [str(col) for col in formatted_chunk.columns]
                rows.append('\t'.join(headers))

                # 添加数据行
                for _, row in formatted_chunk.iterrows():
                    rows.append('\t'.join(row.values))

                return '\n'.join(rows)
            else:
                flat_values = (
                    chunk.astype(str)
                    .replace({'nan': '', 'None': '', 'NaN': ''})
                    .values.flatten()
                )
                return ' '.join(v for v in flat_values if v)

        except Exception as e:
            self.logger.error(f"Error processing chunk: {e}")
            raise