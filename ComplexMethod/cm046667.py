def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        min_p: float = 0.0,
        max_new_tokens: int = 256,
        repetition_penalty: float = 1.0,
        cancel_event = None,
        _adapter_state = None,
    ) -> Generator[str, None, None]:
        """Generate streaming text response (text models only).

        _adapter_state: if not None, the background thread toggles adapters
        before model.generate(), all under _generation_lock.
        """
        if not self.active_model_name:
            yield "Error: No active model"
            return

        model_info = self.models[self.active_model_name]
        model = model_info["model"]
        # For VLMs the stored "tokenizer" is actually the processor.
        # Unwrap to get the real tokenizer so TextIteratorStreamer's
        # skip_prompt / skip_special_tokens work correctly.
        tokenizer = model_info["tokenizer"]
        tokenizer = getattr(tokenizer, "tokenizer", tokenizer)

        try:
            inputs = tokenizer(prompt, return_tensors = "pt").to(model.device)

            from transformers import TextIteratorStreamer
            import threading

            # Use HarmonyTextStreamer for gpt-oss models to properly parse
            # the multi-channel harmony protocol into <think> tags
            if self._is_gpt_oss_model():
                try:
                    streamer = HarmonyTextStreamer(
                        tokenizer,
                        skip_prompt = True,
                        timeout = 0.2,
                    )
                except Exception as e:
                    logger.warning(
                        f"HarmonyTextStreamer init failed, falling back: {e}"
                    )
                    streamer = TextIteratorStreamer(
                        tokenizer,
                        skip_prompt = True,
                        skip_special_tokens = True,
                        timeout = 0.2,
                    )
            else:
                streamer = TextIteratorStreamer(
                    tokenizer,
                    skip_prompt = True,
                    skip_special_tokens = True,
                    timeout = 0.2,
                )

            generation_kwargs = dict(
                **inputs,
                streamer = streamer,
                max_new_tokens = max_new_tokens,
                temperature = temperature,
                top_p = top_p,
                top_k = top_k,
                min_p = min_p,
                repetition_penalty = repetition_penalty,
                do_sample = temperature > 0,
                eos_token_id = tokenizer.eos_token_id,
                pad_token_id = tokenizer.eos_token_id
                if tokenizer.pad_token_id is None
                else tokenizer.pad_token_id,
            )
            if cancel_event is not None:
                from transformers.generation.stopping_criteria import (
                    StoppingCriteria,
                    StoppingCriteriaList,
                )

                class _CancelCriteria(StoppingCriteria):
                    def __init__(self, ev):
                        self.ev = ev

                    def __call__(self, input_ids, scores, **kwargs):
                        return self.ev.is_set()

                generation_kwargs["stopping_criteria"] = StoppingCriteriaList(
                    [_CancelCriteria(cancel_event)]
                )

            def generate_fn():
                with self._generation_lock:
                    try:
                        if _adapter_state is not None:
                            self._apply_adapter_state(_adapter_state)
                        model.generate(**generation_kwargs)
                    except Exception as e:
                        err["msg"] = str(e)
                        logger.error(f"Generation error: {e}")
                    finally:
                        try:
                            streamer.end()
                        except Exception:
                            pass

            err: dict[str, str] = {}
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
                # Only set cancel_event when we exited early (user cancel),
                # NOT on normal completion.  cancel_event is a shared mp.Event
                # — setting it unconditionally would leave a stale cancel
                # signal that could interfere with the next serialized
                # generation request (e.g. in compare mode).
                if cancel_event is not None and not generation_complete:
                    cancel_event.set()
                thread.join(timeout = 10)
                if thread.is_alive():
                    logger.warning(
                        "Generation thread did not exit after cancel/join timeout"
                    )

            if err.get("msg"):
                yield f"Error: {err['msg']}"

        except Exception as e:
            logger.error(f"Error during generation: {e}")
            yield f"Error: {str(e)}"