async def execute(
        self, code: str, timeout: int = 120
    ) -> dict[str, list[str] | str]:
        if not self.ws or self.ws.stream.closed():
            await self._connect()

        msg_id = uuid4().hex
        assert self.ws is not None
        res = await self.ws.write_message(
            json_encode(
                {
                    'header': {
                        'username': '',
                        'version': '5.0',
                        'session': '',
                        'msg_id': msg_id,
                        'msg_type': 'execute_request',
                    },
                    'parent_header': {},
                    'channel': 'shell',
                    'content': {
                        'code': code,
                        'silent': False,
                        'store_history': False,
                        'user_expressions': {},
                        'allow_stdin': False,
                    },
                    'metadata': {},
                    'buffers': {},
                }
            )
        )
        logging.info(f'Executed code in jupyter kernel:\n{res}')

        outputs: list[dict] = []

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

        async def interrupt_kernel() -> None:
            client = AsyncHTTPClient()
            if self.kernel_id is None:
                return
            interrupt_response = await client.fetch(
                f'{self.base_url}/api/kernels/{self.kernel_id}/interrupt',
                method='POST',
                body=json_encode({'kernel_id': self.kernel_id}),
            )
            logging.info(f'Kernel interrupted: {interrupt_response}')

        try:
            execution_done = await asyncio.wait_for(wait_for_messages(), timeout)
        except asyncio.TimeoutError:
            await interrupt_kernel()
            return {'text': f'[Execution timed out ({timeout} seconds).]', 'images': []}

        # Process structured outputs
        text_outputs = []
        image_outputs = []

        for output in outputs:
            if output['type'] == 'text':
                text_outputs.append(output['content'])
            elif output['type'] == 'image':
                image_outputs.append(output['content'])

        if not text_outputs and execution_done:
            text_content = '[Code executed successfully with no output]'
        else:
            text_content = ''.join(text_outputs)

        # Remove ANSI from text content
        text_content = strip_ansi(text_content)

        # Return a dictionary with text content and image URLs
        return {'text': text_content, 'images': image_outputs}