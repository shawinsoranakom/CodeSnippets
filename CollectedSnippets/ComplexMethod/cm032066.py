def begin_comment_source_code(self, chatbot=None, history=None):
        # from toolbox import update_ui_latest_msg
        assert self.path is not None
        assert '.py' in self.path   # must be python source code
        # write_target = self.path + '.revised.py'

        write_content = ""
        # with open(self.path + '.revised.py', 'w+', encoding='utf8') as f:
        while True:
            try:
                # yield from update_ui_latest_msg(f"({self.file_basename}) 正在读取下一段代码片段:\n", chatbot=chatbot, history=history, delay=0)
                next_batch, line_no_start, line_no_end = self.get_next_batch()
                self.observe_window_update(f"正在处理{self.file_basename} - {line_no_start}/{len(self.full_context)}\n")
                # yield from update_ui_latest_msg(f"({self.file_basename}) 处理代码片段:\n\n{next_batch}", chatbot=chatbot, history=history, delay=0)

                hint = None
                MAX_ATTEMPT = 2
                for attempt in range(MAX_ATTEMPT):
                    result = self.tag_code(next_batch, hint)
                    try:
                        successful, hint = self.verify_successful(next_batch, result)
                    except Exception as e:
                        logger.error('ignored exception:\n' + str(e))
                        break
                    if successful:
                        break
                    if attempt == MAX_ATTEMPT - 1:
                        # cannot deal with this, give up
                        result = next_batch
                        break

                # f.write(result)
                write_content += result
            except StopIteration:
                next_batch, line_no_start, line_no_end = [], -1, -1
                return None, write_content