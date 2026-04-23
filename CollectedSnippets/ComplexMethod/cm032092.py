def extract_text(
            self,
            file_path: Union[str, Path],
            columns: Optional[List[str]] = None,
            separator: str = '\n'
    ) -> str:
        """提取文本，支持多工作表"""
        try:
            path = self._validate_file(file_path)
            self.logger.info(f"Processing: {path}")

            reader = self._read_file(path)
            texts = []

            # 处理Excel多工作表
            if isinstance(reader, dict):
                for sheet_name, df in reader.items():
                    sheet_text = self._process_chunk(df, columns, sheet_name)
                    if sheet_text:
                        texts.append(sheet_text)
                return separator.join(texts)

            # 处理单个DataFrame
            elif isinstance(reader, pd.DataFrame):
                return self._process_chunk(reader, columns)

            # 处理DataFrame迭代器
            else:
                with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                    futures = {
                        executor.submit(self._process_chunk, chunk, columns): i
                        for i, chunk in enumerate(reader)
                    }

                    chunk_texts = []
                    for future in as_completed(futures):
                        try:
                            text = future.result()
                            if text:
                                chunk_texts.append((futures[future], text))
                        except Exception as e:
                            self.logger.error(f"Error in chunk {futures[future]}: {e}")

                    # 按块的顺序排序
                    chunk_texts.sort(key=lambda x: x[0])
                    texts = [text for _, text in chunk_texts]

                # 合并文本，保留格式
                if texts and self.config.preserve_format:
                    result = texts[0]  # 第一块包含表头
                    if len(texts) > 1:
                        # 跳过后续块的表头行
                        for text in texts[1:]:
                            result += '\n' + '\n'.join(text.split('\n')[1:])
                    return result
                else:
                    return separator.join(texts)

        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            raise