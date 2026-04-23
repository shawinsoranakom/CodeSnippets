async def __call__(
            self, sections: list[str], prompt_variables: dict[str, Any] | None = None
    ) -> MindMapResult:
        """Call method definition."""
        if prompt_variables is None:
            prompt_variables = {}

        res = []
        token_count = max(self._llm.max_length * 0.8, self._llm.max_length - 512)
        texts = []
        cnt = 0
        tasks = []
        for i in range(len(sections)):
            section_cnt = num_tokens_from_string(sections[i])
            if cnt + section_cnt >= token_count and texts:
                tasks.append(asyncio.create_task(
                    self._process_document("".join(texts), prompt_variables, res)
                ))
                texts = []
                cnt = 0

            texts.append(sections[i])
            cnt += section_cnt
        if texts:
            tasks.append(asyncio.create_task(
                self._process_document("".join(texts), prompt_variables, res)
            ))
        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception as e:
            logging.error(f"Error processing document: {e}")
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        if not res:
            return MindMapResult(output={"id": "root", "children": []})
        merge_json = reduce(self._merge, res)
        if len(merge_json) > 1:
            keys = [re.sub(r"\*+", "", k) for k, v in merge_json.items() if isinstance(v, dict)]
            keyset = set(i for i in keys if i)
            merge_json = {
                "id": "root",
                "children": [
                    {
                        "id": self._key(k),
                        "children": self._be_children(v, keyset)
                    }
                    for k, v in merge_json.items() if isinstance(v, dict) and self._key(k)
                ]
            }
        else:
            k = self._key(list(merge_json.keys())[0])
            merge_json = {"id": k, "children": self._be_children(list(merge_json.items())[0][1], {k})}

        return MindMapResult(output=merge_json)