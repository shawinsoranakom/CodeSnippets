async def event_generator(request: Request):
    global log_buffer  # noqa: PLW0602
    last_read_item = None
    current_not_sent = 0
    while not await request.is_disconnected():
        to_write: list[Any] = []
        with log_buffer.get_write_lock():
            if last_read_item is None:
                last_read_item = log_buffer.buffer[len(log_buffer.buffer) - 1]
            else:
                found_last = False
                for item in log_buffer.buffer:
                    if found_last:
                        to_write.append(item)
                        last_read_item = item
                        continue
                    if item is last_read_item:
                        found_last = True
                        continue

                # in case the last item is nomore in the buffer
                if not found_last:
                    for item in log_buffer.buffer:
                        to_write.append(item)
                        last_read_item = item
        if to_write:
            for ts, msg in to_write:
                yield f"{json.dumps({ts: msg})}\n\n"
        else:
            current_not_sent += 1
            if current_not_sent == NUMBER_OF_NOT_SENT_BEFORE_KEEPALIVE:
                current_not_sent = 0
                yield "keepalive\n\n"

        await asyncio.sleep(1)