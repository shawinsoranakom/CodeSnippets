def run(self):
        """
        这个函数运行在子进程
        """
        # 第一次运行，加载参数
        self.success = False
        self.local_history = []
        if (self.newbing_model is None) or (not self.success):
            # 代理设置
            proxies, NEWBING_COOKIES = get_conf("proxies", "NEWBING_COOKIES")
            if proxies is None:
                self.proxies_https = None
            else:
                self.proxies_https = proxies["https"]

            if (NEWBING_COOKIES is not None) and len(NEWBING_COOKIES) > 100:
                try:
                    cookies = json.loads(NEWBING_COOKIES)
                except:
                    self.success = False
                    tb_str = "\n```\n" + trimmed_format_exc() + "\n```\n"
                    self.child.send(f"[Local Message] NEWBING_COOKIES未填写或有格式错误。")
                    self.child.send("[Fail]")
                    self.child.send("[Finish]")
                    raise RuntimeError(f"NEWBING_COOKIES未填写或有格式错误。")
            else:
                cookies = None

            try:
                self.newbing_model = NewbingChatbot(
                    proxy=self.proxies_https, cookies=cookies
                )
            except:
                self.success = False
                tb_str = "\n```\n" + trimmed_format_exc() + "\n```\n"
                self.child.send(
                    f"[Local Message] 不能加载Newbing组件，请注意Newbing组件已不再维护。{tb_str}"
                )
                self.child.send("[Fail]")
                self.child.send("[Finish]")
                raise RuntimeError(f"不能加载Newbing组件，请注意Newbing组件已不再维护。")

        self.success = True
        try:
            # 进入任务等待状态
            asyncio.run(self.async_run())
        except Exception:
            tb_str = "\n```\n" + trimmed_format_exc() + "\n```\n"
            self.child.send(
                f"[Local Message] Newbing 请求失败，报错信息如下. 如果是与网络相关的问题，建议更换代理协议（推荐http）或代理节点 {tb_str}."
            )
            self.child.send("[Fail]")
            self.child.send("[Finish]")