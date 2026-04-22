async def finish_script(success: bool) -> None:
                status = (
                    ForwardMsg.FINISHED_SUCCESSFULLY
                    if success
                    else ForwardMsg.FINISHED_WITH_COMPILE_ERROR
                )
                finish_msg = create_script_finished_message(status)
                self.enqueue_forward_msg(session_id, finish_msg)
                await self.tick_runtime_loop()