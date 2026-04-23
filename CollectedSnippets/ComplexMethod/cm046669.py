def format_chat_prompt(self, messages: list, system_prompt: str = None) -> str:
        if not self.active_model_name or self.active_model_name not in self.models:
            logger.error("No active model available")
            return ""

        if self.models[self.active_model_name].get("tokenizer") is None:
            logger.error("Tokenizer not loaded for active model")
            return ""

        chat_template_info = self.models[self.active_model_name].get(
            "chat_template_info", {}
        )
        tokenizer = self.models[self.active_model_name]["tokenizer"]
        tokenizer = getattr(tokenizer, "tokenizer", tokenizer)

        chat_messages = []

        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})

        last_role = "system" if system_prompt else None

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role in ["system", "user", "assistant"] and content.strip():
                if role == last_role:
                    logger.debug(
                        f"Skipping consecutive {role} message to maintain alternation"
                    )
                    continue

                if role == "user":
                    import re

                    clean_content = re.sub(r"<[^>]+>", "", content).strip()
                    if clean_content:
                        chat_messages.append({"role": role, "content": clean_content})
                        last_role = role
                elif role == "assistant" and content.strip():
                    chat_messages.append({"role": role, "content": content})
                    last_role = role
                elif role == "system":
                    continue

        if chat_messages and chat_messages[-1]["role"] == "assistant":
            logger.debug(
                "Removing final assistant message to ensure proper alternation"
            )
            chat_messages.pop()

        logger.info(f"Sending {len(chat_messages)} messages to tokenizer:")
        for i, msg in enumerate(chat_messages):
            logger.info(f"  {i}: {msg['role']} - {msg['content'][:50]}...")

        try:
            formatted_prompt = tokenizer.apply_chat_template(
                chat_messages, tokenize = False, add_generation_prompt = True
            )
            logger.info(f"Successfully applied tokenizer's native chat template")
            return formatted_prompt
        except Exception as e:
            error_msg = str(e).lower()
            if (
                "chat_template is not set" in error_msg
                or "no template argument" in error_msg
            ):
                logger.info(
                    f"Base model detected - no built-in chat template available, using fallback formatting"
                )
            else:
                logger.warning(f"Failed to apply tokenizer chat template: {e}")
            logger.debug(
                f"""Failed with messages: {[f"{m['role']}: {m['content'][:30]}..." for m in chat_messages]}"""
            )

        if chat_template_info.get("has_template", False):
            logger.info(
                "Falling back to manual template formatting based on detected patterns"
            )
            template_type = chat_template_info.get("format_type", "generic")
            manual_prompt = self._format_chat_manual(
                chat_messages,
                template_type,
                chat_template_info.get("special_tokens", {}),
            )
            logger.info(f"Manual template result: {manual_prompt[:200]}...")
            return manual_prompt
        else:
            logger.info("Using generic chat formatting for base model")
            return self._format_generic_template(chat_messages, {})