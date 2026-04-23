def _generate_vision_response(
        self,
        messages,
        system_prompt,
        image,
        temperature,
        top_p,
        top_k,
        min_p,
        max_new_tokens,
        repetition_penalty,
        cancel_event = None,
    ) -> Generator[str, None, None]:
        """Handle vision model generation with true token-by-token streaming."""
        model_info = self.models[self.active_model_name]
        model = model_info["model"]
        processor = model_info["processor"]
        # FastVisionModel may return a raw tokenizer (e.g. GemmaTokenizerFast)
        # instead of a Processor for some models. Safe unwrap for tokenize-only ops.
        raw_tokenizer = getattr(processor, "tokenizer", processor)

        # Extract user message
        user_message = ""
        if messages and messages[-1]["role"] == "user":
            import re

            user_message = messages[-1]["content"]
            user_message = re.sub(r"<img[^>]*>", "", user_message).strip()

        if not user_message:
            user_message = "Describe this image." if image else "Hello"

        # Prepare vision messages
        if image:
            user_msg = {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": user_message},
                ],
            }
            if system_prompt:
                vision_messages = [
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": system_prompt}],
                    },
                    user_msg,
                ]
            else:
                vision_messages = [user_msg]

            try:
                input_text = processor.apply_chat_template(
                    vision_messages, add_generation_prompt = True, tokenize = False
                )
            except Exception as e:
                if system_prompt:
                    logger.warning(
                        f"Vision processor for '{self.active_model_name}' may not support "
                        f"system messages; retrying without. Original error: {e}"
                    )
                    vision_messages = [user_msg]
                    input_text = processor.apply_chat_template(
                        vision_messages, add_generation_prompt = True, tokenize = False
                    )
                else:
                    raise
            inputs = processor(
                image,
                input_text,
                add_special_tokens = False,
                return_tensors = "pt",
            ).to(model.device)
        else:
            # Text-only for vision model
            formatted_prompt = self.format_chat_prompt(messages, system_prompt)
            inputs = raw_tokenizer(formatted_prompt, return_tensors = "pt").to(
                model.device
            )

        # Stream with TextIteratorStreamer + background thread
        try:
            from transformers import TextIteratorStreamer
            import threading

            streamer = TextIteratorStreamer(
                raw_tokenizer,
                skip_prompt = True,
                skip_special_tokens = True,
                timeout = 0.2,
            )

            generation_kwargs = dict(
                **inputs,
                streamer = streamer,
                max_new_tokens = max_new_tokens,
                use_cache = True,
                do_sample = temperature > 0,
                temperature = temperature,
                top_p = top_p,
                top_k = top_k,
                min_p = min_p,
            )

            err: dict[str, str] = {}

            def generate_fn():
                with self._generation_lock:
                    try:
                        model.generate(**generation_kwargs)
                    except Exception as e:
                        err["msg"] = str(e)
                        logger.error(f"Vision generation error in thread: {e}")
                    finally:
                        try:
                            streamer.end()
                        except Exception:
                            pass

            thread = threading.Thread(target = generate_fn)
            thread.start()

            output = ""
            from queue import Empty

            generation_complete = False
            try:
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        break
                    try:
                        new_token = next(streamer)
                    except StopIteration:
                        generation_complete = True
                        break
                    except Empty:
                        if not thread.is_alive():
                            generation_complete = True
                            break
                        continue
                    if new_token:
                        output += new_token
                        cleaned = self._clean_generated_text(output)
                        yield cleaned
            finally:
                if cancel_event is not None and not generation_complete:
                    cancel_event.set()
                thread.join(timeout = 10)
                if thread.is_alive():
                    logger.warning(
                        "Vision generation thread did not exit after cancel/join timeout"
                    )

            if err.get("msg"):
                yield f"Error: {err['msg']}"

        except Exception as e:
            logger.error(f"Vision generation error: {e}")
            yield f"Error: {str(e)}"