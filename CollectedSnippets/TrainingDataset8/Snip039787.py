async def send_data_msg() -> None:
                self.enqueue_forward_msg(session_id, data_msg)
                await self.tick_runtime_loop()