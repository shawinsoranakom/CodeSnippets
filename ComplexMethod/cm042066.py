async def fill(
        self,
        *,
        req,
        llm,
        schema="json",
        mode="auto",
        strgy="simple",
        images: Optional[Union[str, list[str]]] = None,
        timeout=USE_CONFIG_TIMEOUT,
        exclude=[],
        function_name: str = None,
    ):
        """Fill the node(s) with mode.

        :param req: Everything we should know when filling node.
        :param llm: Large Language Model with pre-defined system message.
        :param schema: json/markdown, determine example and output format.
         - raw: free form text
         - json: it's easy to open source LLM with json format
         - markdown: when generating code, markdown is always better
        :param mode: auto/children/root
         - auto: automated fill children's nodes and gather outputs, if no children, fill itself
         - children: fill children's nodes and gather outputs
         - root: fill root's node and gather output
        :param strgy: simple/complex
         - simple: run only once
         - complex: run each node
        :param images: the list of image url or base64 for gpt4-v
        :param timeout: Timeout for llm invocation.
        :param exclude: The keys of ActionNode to exclude.
        :return: self
        """
        self.set_llm(llm)
        self.set_context(req)
        if self.schema:
            schema = self.schema

        if mode == FillMode.CODE_FILL.value:
            result = await self.code_fill(context, function_name, timeout)
            self.instruct_content = self.create_class()(**result)
            return self

        elif mode == FillMode.XML_FILL.value:
            context = self.xml_compile(context=self.context)
            result = await self.xml_fill(context, images=images)
            self.instruct_content = self.create_class()(**result)
            return self

        elif mode == FillMode.SINGLE_FILL.value:
            result = await self.single_fill(context, images=images)
            self.instruct_content = self.create_class()(**result)
            return self

        if strgy == "simple":
            return await self.simple_fill(schema=schema, mode=mode, images=images, timeout=timeout, exclude=exclude)
        elif strgy == "complex":
            # 这里隐式假设了拥有children
            tmp = {}
            for _, i in self.children.items():
                if exclude and i.key in exclude:
                    continue
                child = await i.simple_fill(schema=schema, mode=mode, images=images, timeout=timeout, exclude=exclude)
                tmp.update(child.instruct_content.model_dump())
            cls = self._create_children_class()
            self.instruct_content = cls(**tmp)
            return self