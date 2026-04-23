async def run(context, max_token, temperature, top_p, addr, port):
    params = {
        'max_new_tokens': max_token,
        'do_sample': True,
        'temperature': temperature,
        'top_p': top_p,
        'typical_p': 1,
        'repetition_penalty': 1.05,
        'encoder_repetition_penalty': 1.0,
        'top_k': 0,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': True,
        'seed': -1,
    }
    session = random_hash()

    async with websockets.connect(f"ws://{addr}:{port}/queue/join") as websocket:
        while content := json.loads(await websocket.recv()):
            #Python3.10 syntax, replace with if elif on older
            if content["msg"] ==  "send_hash":
                await websocket.send(json.dumps({
                    "session_hash": session,
                    "fn_index": 12
                }))
            elif content["msg"] ==  "estimation":
                pass
            elif content["msg"] ==  "send_data":
                await websocket.send(json.dumps({
                    "session_hash": session,
                    "fn_index": 12,
                    "data": [
                        context,
                        params['max_new_tokens'],
                        params['do_sample'],
                        params['temperature'],
                        params['top_p'],
                        params['typical_p'],
                        params['repetition_penalty'],
                        params['encoder_repetition_penalty'],
                        params['top_k'],
                        params['min_length'],
                        params['no_repeat_ngram_size'],
                        params['num_beams'],
                        params['penalty_alpha'],
                        params['length_penalty'],
                        params['early_stopping'],
                        params['seed'],
                    ]
                }))
            elif content["msg"] ==  "process_starts":
                pass
            elif content["msg"] in ["process_generating", "process_completed"]:
                yield content["output"]["data"][0]
                # You can search for your desired end indicator and
                #  stop generation by closing the websocket here
                if (content["msg"] == "process_completed"):
                    break