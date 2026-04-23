def main_process_ui_control(self, txt, create_or_resume) -> str:
        # ⭐ 主进程
        if create_or_resume == 'create':
            self.cnt = 1
            self.parent_conn = self.launch_subprocess_with_pipe() # ⭐⭐⭐
        repeated, cmd_to_autogen = self.send_command(txt)
        if txt == 'exit':
            self.chatbot.append([f"结束", "结束信号已明确，终止AutoGen程序。"])
            yield from update_ui(chatbot=self.chatbot, history=self.history)
            self.terminate()
            return "terminate"

        # patience = 10

        while True:
            time.sleep(0.5)
            if not self.alive:
                # the heartbeat watchdog might have it killed
                self.terminate()
                return "terminate"
            if self.parent_conn.poll():
                self.feed_heartbeat_watchdog()
                if "[GPT-Academic] 等待中" in self.chatbot[-1][-1]:
                    self.chatbot.pop(-1)  # remove the last line
                if "等待您的进一步指令" in self.chatbot[-1][-1]:
                    self.chatbot.pop(-1)  # remove the last line
                if '[GPT-Academic] 等待中' in self.chatbot[-1][-1]:
                    self.chatbot.pop(-1)    # remove the last line
                msg = self.parent_conn.recv() # PipeCom
                if msg.cmd == "done":
                    self.chatbot.append([f"结束", msg.content])
                    self.cnt += 1
                    yield from update_ui(chatbot=self.chatbot, history=self.history)
                    self.terminate()
                    break
                if msg.cmd == "show":
                    yield from self.overwatch_workdir_file_change()
                    notice = ""
                    if repeated: notice = "（自动忽略重复的输入）"
                    self.chatbot.append([f"运行阶段-{self.cnt}（上次用户反馈输入为: 「{cmd_to_autogen}」{notice}", msg.content])
                    self.cnt += 1
                    yield from update_ui(chatbot=self.chatbot, history=self.history)
                if msg.cmd == "interact":
                    yield from self.overwatch_workdir_file_change()
                    self.chatbot.append([f"程序抵达用户反馈节点.", msg.content +
                                         "\n\n等待您的进一步指令." +
                                         "\n\n(1) 一般情况下您不需要说什么, 清空输入区, 然后直接点击“提交”以继续. " +
                                         "\n\n(2) 如果您需要补充些什么, 输入要反馈的内容, 直接点击“提交”以继续. " +
                                         "\n\n(3) 如果您想终止程序, 输入exit, 直接点击“提交”以终止AutoGen并解锁. "
                    ])
                    yield from update_ui(chatbot=self.chatbot, history=self.history)
                    # do not terminate here, leave the subprocess_worker instance alive
                    return "wait_feedback"
            else:
                self.feed_heartbeat_watchdog()
                if '[GPT-Academic] 等待中' not in self.chatbot[-1][-1]:
                    # begin_waiting_time = time.time()
                    self.chatbot.append(["[GPT-Academic] 等待AutoGen执行结果 ...", "[GPT-Academic] 等待中"])
                self.chatbot[-1] = [self.chatbot[-1][0], self.chatbot[-1][1].replace("[GPT-Academic] 等待中", "[GPT-Academic] 等待中.")]
                yield from update_ui(chatbot=self.chatbot, history=self.history)
                # if time.time() - begin_waiting_time > patience:
                #     self.chatbot.append([f"结束", "等待超时, 终止AutoGen程序。"])
                #     yield from update_ui(chatbot=self.chatbot, history=self.history)
                #     self.terminate()
                #     return "terminate"

        self.terminate()
        return "terminate"