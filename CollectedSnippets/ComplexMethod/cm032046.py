def _process_single_file_with_timeout(self, file_info: Tuple[str, str], mutable_status: List) -> List[FileFragment]:
        """包装了超时控制的文件处理函数"""

        def timeout_handler():
            thread = threading.current_thread()
            if hasattr(thread, '_timeout_occurred'):
                thread._timeout_occurred = True

        # 设置超时标记
        thread = threading.current_thread()
        thread._timeout_occurred = False

        # 设置超时时间为30秒，给予更多处理时间
        TIMEOUT_SECONDS = 30
        timer = threading.Timer(TIMEOUT_SECONDS, timeout_handler)
        timer.start()

        try:
            fp, project_folder = file_info
            fragments = []

            # 定期检查是否超时
            def check_timeout():
                if hasattr(thread, '_timeout_occurred') and thread._timeout_occurred:
                    raise TimeoutError(f"处理文件 {os.path.basename(fp)} 超时（{TIMEOUT_SECONDS}秒）")

            # 更新状态
            mutable_status[0] = "检查文件大小"
            mutable_status[1] = time.time()
            check_timeout()

            # 文件大小检查
            if os.path.getsize(fp) > self.max_file_size:
                self.failed_files.append((fp, f"文件过大：超过{self.max_file_size / 1024 / 1024}MB"))
                mutable_status[2] = "文件过大"
                return fragments

            # 更新状态
            mutable_status[0] = "提取文件内容"
            mutable_status[1] = time.time()

            # 提取内容 - 使用单独的超时控制
            content = None
            extract_start_time = time.time()
            try:
                while True:
                    check_timeout()  # 检查全局超时

                    # 检查提取过程是否超时（10秒）
                    if time.time() - extract_start_time > 10:
                        raise TimeoutError("文件内容提取超时（10秒）")

                    try:
                        content = extract_text(fp)
                        break
                    except Exception as e:
                        if "timeout" in str(e).lower():
                            continue  # 如果是临时超时，重试
                        raise  # 其他错误直接抛出

            except Exception as e:
                self.failed_files.append((fp, f"文件读取失败：{str(e)}"))
                mutable_status[2] = "读取失败"
                return fragments

            if content is None:
                self.failed_files.append((fp, "文件解析失败：不支持的格式或文件损坏"))
                mutable_status[2] = "格式不支持"
                return fragments
            elif not content.strip():
                self.failed_files.append((fp, "文件内容为空"))
                mutable_status[2] = "内容为空"
                return fragments

            check_timeout()

            # 更新状态
            mutable_status[0] = "分割文本"
            mutable_status[1] = time.time()

            # 分割文本 - 添加超时检查
            split_start_time = time.time()
            try:
                while True:
                    check_timeout()  # 检查全局超时

                    # 检查分割过程是否超时（5秒）
                    if time.time() - split_start_time > 5:
                        raise TimeoutError("文本分割超时（5秒）")

                    paper_fragments = breakdown_text_to_satisfy_token_limit(
                        txt=content,
                        limit=self._get_token_limit(),
                        llm_model=self.llm_kwargs['llm_model']
                    )
                    break

            except Exception as e:
                self.failed_files.append((fp, f"文本分割失败：{str(e)}"))
                mutable_status[2] = "分割失败"
                return fragments

            # 处理片段
            rel_path = os.path.relpath(fp, project_folder)
            for i, frag in enumerate(paper_fragments):
                check_timeout()  # 每处理一个片段检查一次超时
                if frag.strip():
                    fragments.append(FileFragment(
                        file_path=fp,
                        content=frag,
                        rel_path=rel_path,
                        fragment_index=i,
                        total_fragments=len(paper_fragments)
                    ))

            mutable_status[2] = "处理完成"
            return fragments

        except TimeoutError as e:
            self.failed_files.append((fp, str(e)))
            mutable_status[2] = "处理超时"
            return []
        except Exception as e:
            self.failed_files.append((fp, f"处理失败：{str(e)}"))
            mutable_status[2] = "处理异常"
            return []
        finally:
            timer.cancel()