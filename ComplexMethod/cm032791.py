async def _research(self, chunk_info, question, query, depth=3, callback=None):
        if depth == 0:
            #if callback:
            #    await callback("Reach the max search depth.")
            return ""
        if callback:
            await callback(f"Searching by `{query}`...")
        st = timer()
        ret = await self._retrieve_information(query)
        if callback:
            await callback("Retrieval %d results in %.1fms"%(len(ret["chunks"]), (timer()-st)*1000))
        await self._async_update_chunk_info(chunk_info, ret)
        ret = kb_prompt(ret, self.chat_mdl.max_length*0.5)

        if callback:
            await callback("Checking the sufficiency for retrieved information.")
        suff = await sufficiency_check(self.chat_mdl, question, ret)
        if suff["is_sufficient"]:
            if callback:
                await callback(f"Yes, the retrieved information is sufficient for '{question}'.")
            return ret

        #if callback:
        #    await callback("The retrieved information is not sufficient. Planing next steps...")
        succ_question_info = await multi_queries_gen(self.chat_mdl, question, query, suff["missing_information"], ret)
        if callback:
            await callback("Next step is to search for the following questions:</br> - " + "</br> - ".join(step["question"] for step in succ_question_info["questions"]))
        steps = []
        for step in succ_question_info["questions"]:
            steps.append(asyncio.create_task(self._research(chunk_info, step["question"], step["query"], depth-1, callback)))
        results = await asyncio.gather(*steps, return_exceptions=True)
        return "\n".join([str(r) for r in results])