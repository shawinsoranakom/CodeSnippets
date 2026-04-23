async def wait_for_messages() -> bool:
            execution_done = False
            while not execution_done:
                assert self.ws is not None
                msg = await self.ws.read_message()
                if msg is None:
                    continue
                msg_dict = json_decode(msg)
                msg_type = msg_dict['msg_type']
                parent_msg_id = msg_dict['parent_header'].get('msg_id', None)

                if parent_msg_id != msg_id:
                    continue

                if os.environ.get('DEBUG'):
                    logging.info(
                        f'MSG TYPE: {msg_type.upper()} DONE:{execution_done}\nCONTENT: {msg_dict["content"]}'
                    )

                if msg_type == 'error':
                    traceback = '\n'.join(msg_dict['content']['traceback'])
                    outputs.append({'type': 'text', 'content': traceback})
                    execution_done = True
                elif msg_type == 'stream':
                    outputs.append(
                        {'type': 'text', 'content': msg_dict['content']['text']}
                    )
                elif msg_type in ['execute_result', 'display_data']:
                    outputs.append(
                        {
                            'type': 'text',
                            'content': msg_dict['content']['data']['text/plain'],
                        }
                    )
                    if 'image/png' in msg_dict['content']['data']:
                        # Store image data in structured format
                        image_url = f'data:image/png;base64,{msg_dict["content"]["data"]["image/png"]}'
                        outputs.append({'type': 'image', 'content': image_url})

                elif msg_type == 'execute_reply':
                    execution_done = True
            return execution_done