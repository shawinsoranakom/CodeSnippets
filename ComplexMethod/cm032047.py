def prepare_fragments(self, project_folder: str, file_paths: List[str]) -> Generator:
        import concurrent.futures

        from concurrent.futures import ThreadPoolExecutor
        from typing import Generator, List
        """并行准备所有文件的处理片段"""
        all_fragments = []
        total_files = len(file_paths)

        # 配置参数
        self.refresh_interval = 0.2  # UI刷新间隔
        self.watch_dog_patience = 5  # 看门狗超时时间
        self.max_file_size = 10 * 1024 * 1024  # 10MB限制
        self.max_workers = min(32, len(file_paths))  # 最多32个线程

        # 创建有超时控制的线程池
        executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # 用于跨线程状态传递的可变列表 - 增加文件名信息
        mutable_status_array = [["等待中", time.time(), "pending", file_path] for file_path in file_paths]

        # 创建文件处理任务
        file_infos = [(fp, project_folder) for fp in file_paths]

        # 提交所有任务，使用带超时控制的处理函数
        futures = [
            executor.submit(
                self._process_single_file_with_timeout,
                file_info,
                mutable_status_array[i]
            ) for i, file_info in enumerate(file_infos)
        ]

        # 更新UI的计数器
        cnt = 0

        try:
            # 监控任务执行
            while True:
                time.sleep(self.refresh_interval)
                cnt += 1

                # 检查任务完成状态
                worker_done = [f.done() for f in futures]

                # 更新状态显示
                status_str = ""
                for i, (status, timestamp, desc, file_path) in enumerate(mutable_status_array):
                    # 获取文件名（去掉路径）
                    file_name = os.path.basename(file_path)
                    if worker_done[i]:
                        status_str += f"文件 {file_name}: {desc}\n\n"
                    else:
                        status_str += f"文件 {file_name}: {status} {desc}\n\n"

                # 更新UI
                self.chatbot[-1] = [
                    "处理进度",
                    f"正在处理文件...\n\n{status_str}" + "." * (cnt % 10 + 1)
                ]
                yield from update_ui(chatbot=self.chatbot, history=self.history)

                # 检查是否所有任务完成
                if all(worker_done):
                    break

        finally:
            # 确保线程池正确关闭
            executor.shutdown(wait=False)

        # 收集结果
        processed_files = 0
        for future in futures:
            try:
                fragments = future.result(timeout=0.1)  # 给予一个短暂的超时时间来获取结果
                all_fragments.extend(fragments)
                processed_files += 1
            except concurrent.futures.TimeoutError:
                # 处理获取结果超时
                file_index = futures.index(future)
                self.failed_files.append((file_paths[file_index], "结果获取超时"))
                continue
            except Exception as e:
                # 处理其他异常
                file_index = futures.index(future)
                self.failed_files.append((file_paths[file_index], f"未知错误：{str(e)}"))
                continue

        # 最终进度更新
        self.chatbot.append([
            "文件处理完成",
            f"成功处理 {len(all_fragments)} 个片段，失败 {len(self.failed_files)} 个文件"
        ])
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        return all_fragments