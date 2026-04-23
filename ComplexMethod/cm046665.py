def generate_audio_input_response(
        self,
        messages,
        system_prompt,
        audio_array,
        temperature,
        top_p,
        top_k,
        min_p,
        max_new_tokens,
        repetition_penalty,
        cancel_event = None,
    ) -> Generator[str, None, None]:
        """Handle audio input (ASR) generation — accepts audio numpy array, streams text output.

        Uses processor.apply_chat_template with audio embedded in messages (Gemma 3n pattern).
        """
        import threading
        import numpy as np

        model_info = self.models[self.active_model_name]
        model = model_info["model"]
        processor = model_info.get("processor") or model_info.get("tokenizer")
        raw_tokenizer = getattr(processor, "tokenizer", processor)

        # Extract last user text — default matches notebook prompt
        user_text = "Please transcribe this audio."
        if messages:
            for msg in reversed(messages):
                if msg["role"] == "user" and msg.get("content"):
                    user_text = msg["content"]
                    break

        # Use ASR-specific system prompt if user hasn't set a custom one
        if not system_prompt:
            system_prompt = "You are an assistant that transcribes speech accurately."

        # Build messages in Gemma 3n format — audio goes INTO apply_chat_template
        audio_messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {
                "role": "user",
                "content": [
                    {"type": "audio", "audio": audio_array},
                    {"type": "text", "text": user_text},
                ],
            },
        ]

        # apply_chat_template handles audio embedding + tokenization in one step
        inputs = processor.apply_chat_template(
            audio_messages,
            add_generation_prompt = True,
            tokenize = True,
            return_dict = True,
            return_tensors = "pt",
            truncation = False,
        ).to(model.device)

        try:
            from transformers import TextIteratorStreamer
            from queue import Empty

            streamer = TextIteratorStreamer(
                raw_tokenizer,
                skip_prompt = True,
                skip_special_tokens = True,
                timeout = 0.2,
            )

            # Notebook uses do_sample=False for ASR (greedy decoding for accuracy)
            generation_kwargs = dict(
                **inputs,
                streamer = streamer,
                max_new_tokens = max_new_tokens,
                use_cache = True,
                do_sample = False,
            )

            err: dict[str, str] = {}

            def generate_fn():
                with self._generation_lock:
                    try:
                        model.generate(**generation_kwargs)
                    except Exception as e:
                        err["msg"] = str(e)
                        logger.error(f"Audio input generation error in thread: {e}")
                    finally:
                        try:
                            streamer.end()
                        except Exception:
                            pass

            thread = threading.Thread(target = generate_fn)
            thread.start()

            output = ""
            try:
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        break
                    try:
                        new_token = next(streamer)
                    except StopIteration:
                        break
                    except Empty:
                        if not thread.is_alive():
                            break
                        continue
                    if new_token:
                        output += new_token
                        yield new_token
            finally:
                if cancel_event is not None:
                    cancel_event.set()
                thread.join(timeout = 10)
                if thread.is_alive():
                    logger.warning(
                        "Audio input generation thread did not exit after cancel/join timeout"
                    )

            if err.get("msg"):
                yield f"Error: {err['msg']}"

        except Exception as e:
            logger.error(f"Audio input generation error: {e}")
            yield f"Error: {str(e)}"