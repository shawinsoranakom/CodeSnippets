def queue_consumer(self, queue_name, group_name, consumer_name, msg_id=b">") -> RedisMsg:
        """https://redis.io/docs/latest/commands/xreadgroup/"""
        for _ in range(3):
            try:

                try:
                    group_info = self.REDIS.xinfo_groups(queue_name)
                    if not any(gi["name"] == group_name for gi in group_info):
                        self.REDIS.xgroup_create(queue_name, group_name, id="0", mkstream=True)
                except redis.exceptions.ResponseError as e:
                    if "no such key" in str(e).lower():
                        self.REDIS.xgroup_create(queue_name, group_name, id="0", mkstream=True)
                    elif "busygroup" in str(e).lower():
                        logging.warning("Group already exists, continue.")
                        pass
                    else:
                        raise

                args = {
                    "groupname": group_name,
                    "consumername": consumer_name,
                    "count": 1,
                    "block": 5,
                    "streams": {queue_name: msg_id},
                }
                messages = self.REDIS.xreadgroup(**args)
                if not messages:
                    return None
                stream, element_list = messages[0]
                if not element_list:
                    return None
                msg_id, payload = element_list[0]
                res = RedisMsg(self.REDIS, queue_name, group_name, msg_id, payload)
                return res
            except Exception as e:
                if str(e) == 'no such key':
                    pass
                else:
                    logging.exception(
                        "RedisDB.queue_consumer "
                        + str(queue_name)
                        + " got exception: "
                        + str(e)
                    )
                    self.__open__()
        return None