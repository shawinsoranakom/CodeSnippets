async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        msg = self.rc.memory.get(k=1)[0]
        if isinstance(msg.instruct_content, Report):
            instruct_content = msg.instruct_content
            topic = instruct_content.topic
        else:
            topic = msg.content

        research_system_text = self.research_system_text(topic, todo)
        if isinstance(todo, CollectLinks):
            links = await todo.run(topic, 4, 4)
            ret = Message(
                content="", instruct_content=Report(topic=topic, links=links), role=self.profile, cause_by=todo
            )
        elif isinstance(todo, WebBrowseAndSummarize):
            links = instruct_content.links
            todos = (
                todo.run(*url, query=query, system_text=research_system_text) for (query, url) in links.items() if url
            )
            if self.enable_concurrency:
                summaries = await asyncio.gather(*todos)
            else:
                summaries = [await i for i in todos]
            summaries = list((url, summary) for i in summaries for (url, summary) in i.items() if summary)
            ret = Message(
                content="", instruct_content=Report(topic=topic, summaries=summaries), role=self.profile, cause_by=todo
            )
        else:
            summaries = instruct_content.summaries
            summary_text = "\n---\n".join(f"url: {url}\nsummary: {summary}" for (url, summary) in summaries)
            content = await self.rc.todo.run(topic, summary_text, system_text=research_system_text)
            ret = Message(
                content="",
                instruct_content=Report(topic=topic, content=content),
                role=self.profile,
                cause_by=self.rc.todo,
            )
        self.rc.memory.add(ret)
        return ret