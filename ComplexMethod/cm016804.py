def run(self, graph, partial_execution_targets=None):
        prompt = graph.finalize()
        for node in graph.nodes.values():
            if node.class_type == 'SaveImage':
                node.inputs['filename_prefix'] = self.test_name

        prompt_id = self.queue_prompt(prompt, partial_execution_targets)['prompt_id']
        result = RunResult(prompt_id)
        while True:
            out = self.ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['prompt_id'] != prompt_id:
                        continue
                    if data['node'] is None:
                        break
                    result.runs[data['node']] = True
                elif message['type'] == 'execution_error':
                    raise Exception(message['data'])
                elif message['type'] == 'execution_cached':
                    if message['data']['prompt_id'] == prompt_id:
                        cached_nodes = message['data'].get('nodes', [])
                        for node_id in cached_nodes:
                            result.cached[node_id] = True

        history = self.get_history(prompt_id)[prompt_id]
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            result.outputs[node_id] = node_output
            images_output = []
            if 'images' in node_output:
                for image in node_output['images']:
                    image_data = self.get_image(image['filename'], image['subfolder'], image['type'])
                    image_obj = Image.open(BytesIO(image_data))
                    images_output.append(image_obj)
                node_output['image_objects'] = images_output

        return result