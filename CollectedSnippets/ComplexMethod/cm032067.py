def exe_autogen(self, input):
        # ⭐⭐ run in subprocess
        input = input.content
        code_execution_config = {"work_dir": self.autogen_work_dir, "use_docker": self.use_docker}
        agents = self.define_agents()
        user_proxy = None
        assistant = None
        for agent_kwargs in agents:
            agent_cls = agent_kwargs.pop('cls')
            kwargs = {
                'llm_config':self.llm_kwargs,
                'code_execution_config':code_execution_config
            }
            kwargs.update(agent_kwargs)
            agent_handle = agent_cls(**kwargs)
            agent_handle._print_received_message = lambda a,b: self.gpt_academic_print_override(agent_kwargs, a, b)
            for d in agent_handle._reply_func_list:
                if hasattr(d['reply_func'],'__name__') and d['reply_func'].__name__ == 'generate_oai_reply':
                    d['reply_func'] = gpt_academic_generate_oai_reply
            if agent_kwargs['name'] == 'user_proxy':
                agent_handle.get_human_input = lambda a: self.gpt_academic_get_human_input(user_proxy, a)
                user_proxy = agent_handle
            if agent_kwargs['name'] == 'assistant': assistant = agent_handle
        try:
            if user_proxy is None or assistant is None: raise Exception("用户代理或助理代理未定义")
            with ProxyNetworkActivate("AutoGen"):
                user_proxy.initiate_chat(assistant, message=input)
        except Exception as e:
            tb_str = '```\n' + trimmed_format_exc() + '```'
            self.child_conn.send(PipeCom("done", "AutoGen 执行失败: \n\n" + tb_str))