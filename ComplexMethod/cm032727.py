def callback(self, component_name: str, progress: float | int | None = None, message: str = "") -> None:
        from common.exceptions import TaskCanceledException
        log_key = f"{self._flow_id}-{self.task_id}-logs"
        timestamp = timer()
        if has_canceled(self.task_id):
            progress = -1
            message += "[CANCEL]"
        try:
            bin = REDIS_CONN.get(log_key)
            obj = json.loads(bin.encode("utf-8"))
            if obj:
                if obj[-1]["component_id"] == component_name:
                    obj[-1]["trace"].append(
                        {
                            "progress": progress,
                            "message": message,
                            "datetime": datetime.datetime.now().strftime("%H:%M:%S"),
                            "timestamp": timestamp,
                            "elapsed_time": timestamp - obj[-1]["trace"][-1]["timestamp"],
                        }
                    )
                else:
                    obj.append(
                        {
                            "component_id": component_name,
                            "trace": [{"progress": progress, "message": message, "datetime": datetime.datetime.now().strftime("%H:%M:%S"), "timestamp": timestamp, "elapsed_time": 0}],
                        }
                    )
            else:
                obj = [
                    {
                        "component_id": component_name,
                        "trace": [{"progress": progress, "message": message, "datetime": datetime.datetime.now().strftime("%H:%M:%S"), "timestamp": timestamp, "elapsed_time": 0}],
                    }
                ]
            if component_name != "END" and self._doc_id and self.task_id:
                percentage = 1.0 / len(self.components.items())
                finished = 0.0
                for o in obj:
                    for t in o["trace"]:
                        if t["progress"] < 0:
                            finished = -1
                            break
                    if finished < 0:
                        break
                    finished += o["trace"][-1]["progress"] * percentage

                msg = ""
                if len(obj[-1]["trace"]) == 1:
                    msg += f"\n-------------------------------------\n[{self.get_component_name(o['component_id'])}]:\n"
                t = obj[-1]["trace"][-1]
                msg += "%s: %s\n" % (t["datetime"], t["message"])
                TaskService.update_progress(self.task_id, {"progress": finished, "progress_msg": msg})
            elif component_name == "END" and not self._doc_id:
                obj[-1]["trace"][-1]["dsl"] = json.loads(str(self))
            REDIS_CONN.set_obj(log_key, obj, 60 * 30)

        except Exception as e:
            logging.exception(e)

        if has_canceled(self.task_id):
            raise TaskCanceledException(message)