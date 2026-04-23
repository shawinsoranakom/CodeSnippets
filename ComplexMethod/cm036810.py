async def single_request():
        while not state.stop_requesting:
            try:
                response = await client.completions.create(
                    model=MODEL_NAME,
                    prompt="Write a story: ",
                    max_tokens=200,
                )
                if sigterm_sent is not None and sigterm_sent.is_set():
                    state.requests_after_sigterm += 1
                # Check if any choice has finish_reason='abort'
                if any(choice.finish_reason == "abort" for choice in response.choices):
                    state.aborted_requests += 1
            except openai.APIStatusError as e:
                if e.status_code == 503:
                    state.got_503 = True
                elif e.status_code == 500:
                    state.got_500 = True
                else:
                    state.errors.append(f"API error: {e}")
            except (openai.APIConnectionError, httpx.RemoteProtocolError):
                state.connection_errors += 1
                if sigterm_sent is not None and sigterm_sent.is_set():
                    break
            except Exception as e:
                state.errors.append(f"Unexpected error: {e}")
                break
            await asyncio.sleep(0.01)