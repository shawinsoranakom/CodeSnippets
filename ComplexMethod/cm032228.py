async def wait_message_to_send(queue_back_to_client: asyncio.Queue, terminate_event: asyncio.Event):
            """
            等待并发送消息到客户端

            持续监听消息队列，将消息序列化后发送给客户端。

            参数:
                queue_back_to_client: 发送给客户端的消息队列
            """
            # 🕜 wait message to send away -> front end
            msg_cnt = 0
            try:
                while True:

                    ################
                    # get message and check terminate
                    while True:
                        try:
                            if terminate_event.is_set():
                                msg = TERMINATE_MSG
                                break
                            else:
                                msg: UserInterfaceMsg = await asyncio.wait_for(queue_back_to_client.get(), timeout=0.25)
                                break
                        except asyncio.TimeoutError:
                            continue  # 继续检查条件
                    if msg.function == TERMINATE_MSG.function:
                        logger.info("Received terminate message, skip this message and stopping wait_message_to_send.")
                        break
                    ################


                    msg_cnt += 1
                    if websocket.application_state != WebSocketState.CONNECTED:
                        break
                    msg.special_kwargs['uuid'] = uuid.uuid4().hex
                    print(msg)
                    await websocket.send_bytes(msg.model_dump_json())
            except Exception as e:
                logger.exception(f"Error in wait_message_to_send: {e}")
                raise e