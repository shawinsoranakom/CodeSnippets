async def post_prompt(request):
            logging.info("got prompt")
            json_data =  await request.json()
            json_data = self.trigger_on_prompt(json_data)

            if "number" in json_data:
                number = float(json_data['number'])
            else:
                number = self.number
                if "front" in json_data:
                    if json_data['front']:
                        number = -number

                self.number += 1

            if "prompt" in json_data:
                prompt = json_data["prompt"]
                prompt_id = str(json_data.get("prompt_id", uuid.uuid4()))

                partial_execution_targets = None
                if "partial_execution_targets" in json_data:
                    partial_execution_targets = json_data["partial_execution_targets"]

                self.node_replace_manager.apply_replacements(prompt)

                valid = await execution.validate_prompt(prompt_id, prompt, partial_execution_targets)
                extra_data = {}
                if "extra_data" in json_data:
                    extra_data = json_data["extra_data"]

                if "client_id" in json_data:
                    extra_data["client_id"] = json_data["client_id"]
                if valid[0]:
                    outputs_to_execute = valid[2]
                    sensitive = {}
                    for sensitive_val in execution.SENSITIVE_EXTRA_DATA_KEYS:
                        if sensitive_val in extra_data:
                            sensitive[sensitive_val] = extra_data.pop(sensitive_val)
                    extra_data["create_time"] = int(time.time() * 1000)  # timestamp in milliseconds
                    self.prompt_queue.put((number, prompt_id, prompt, extra_data, outputs_to_execute, sensitive))
                    response = {"prompt_id": prompt_id, "number": number, "node_errors": valid[3]}
                    return web.json_response(response)
                else:
                    logging.warning("invalid prompt: {}".format(valid[1]))
                    return web.json_response({"error": valid[1], "node_errors": valid[3]}, status=400)
            else:
                error = {
                    "type": "no_prompt",
                    "message": "No prompt provided",
                    "details": "No prompt provided",
                    "extra_info": {}
                }
                return web.json_response({"error": error, "node_errors": {}}, status=400)