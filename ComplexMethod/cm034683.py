async def __load_actions(cls, html):
        def pars_children(data):
            data = data["children"]
            if len(data) < 4:
                return
            if data[1] in ["div", "defs", "style", "script"]:
                return
            if data[0] == "$":
                pars_data(data[3])
            else:
                for child in data:
                    if isinstance(child, list) and len(data) >= 4:
                        pars_data(child[3])

        def pars_data(data):
            if not isinstance(data, (list, dict)):
                return
            if isinstance(data, dict):
                json_data = data
            elif data[0] == "$":
                if data[1] in ["div", "defs", "style", "script"]:
                    return
                json_data = data[3]
            else:
                return
            if not json_data:
                return
            if 'userState' in json_data:
                debug.log(json_data)
            elif 'initialModels' in json_data:
                models = json_data["initialModels"]
                cls.load_models(models)
            elif 'children' in json_data:
                pars_children(json_data)

        line_pattern = re.compile("^([0-9a-fA-F]+):(.*)")
        pattern = r'self\.__next_f\.push\((\[[\s\S]*?\])\)(?=<\/script>)'
        matches = re.findall(pattern, html)
        for match in matches:
            # Parse the JSON array
            data = json.loads(match)
            for chunk in data[1].split("\n"):
                match = line_pattern.match(chunk)
                if not match:
                    continue
                chunk_id, chunk_data = match.groups()
                if chunk_data.startswith("I["):
                    data = json.loads(chunk_data[1:])
                    async with StreamSession() as session:
                        if "Evaluation" == data[2]:
                            js_files = dict(zip(data[1][::2], data[1][1::2]))
                            for js_id, js in list(js_files.items())[::-1]:
                                js_url = f"{cls.url}/_next/{js}"
                                async with session.get(js_url) as js_response:
                                    js_text = await js_response.text()
                                    if "createServerReference" in js_text:
                                        cls.__extract_actions(js_text)

                elif chunk_data.startswith(("[", "{")):
                    try:
                        data = json.loads(chunk_data)
                        pars_data(data)
                    except json.decoder.JSONDecodeError:
                        ...