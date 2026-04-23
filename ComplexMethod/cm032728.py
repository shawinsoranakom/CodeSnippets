async def run(self, **kwargs):
        log_key = f"{self._flow_id}-{self.task_id}-logs"
        try:
            REDIS_CONN.set_obj(log_key, [], 60 * 10)
        except Exception as e:
            logging.exception(e)
        self.error = ""
        if not self.path:
            self.path.append("File")
            cpn_obj = self.get_component_obj(self.path[0])
            await cpn_obj.invoke(**kwargs)
            if cpn_obj.error():
                self.error = "[ERROR]" + cpn_obj.error()
                self.callback(cpn_obj.component_name, -1, self.error)

        if self._doc_id:
            TaskService.update_progress(self.task_id, {
                "progress": random.randint(0, 5) / 100.0,
                "progress_msg": "Start the pipeline...",
                "begin_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

        idx = len(self.path) - 1
        cpn_obj = self.get_component_obj(self.path[idx])
        idx += 1
        self.path.extend(cpn_obj.get_downstream())

        while idx < len(self.path) and not self.error:
            last_cpn = self.get_component_obj(self.path[idx - 1])
            cpn_obj = self.get_component_obj(self.path[idx])

            async def invoke():
                nonlocal last_cpn, cpn_obj
                await cpn_obj.invoke(**last_cpn.output())
                #if inspect.iscoroutinefunction(cpn_obj.invoke):
                #    await cpn_obj.invoke(**last_cpn.output())
                #else:
                #    cpn_obj.invoke(**last_cpn.output())

            tasks = []
            tasks.append(asyncio.create_task(invoke()))
            await asyncio.gather(*tasks)

            if cpn_obj.error():
                self.error = "[ERROR]" + cpn_obj.error()
                self.callback(cpn_obj._id, -1, self.error)
                break
            idx += 1
            self.path.extend(cpn_obj.get_downstream())

        self.callback("END", 1 if not self.error else -1, json.dumps(self.get_component_obj(self.path[-1]).output(), ensure_ascii=False))

        if not self.error:
            return self.get_component_obj(self.path[-1]).output()

        TaskService.update_progress(self.task_id, {
            "progress": -1,
            "progress_msg": f"[ERROR]: {self.error}"})

        return {}