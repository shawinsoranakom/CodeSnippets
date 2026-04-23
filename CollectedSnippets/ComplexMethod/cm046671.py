def _load_chat_template_info(self, model_name: str):
        if model_name not in self.models or not self.models[model_name].get(
            "tokenizer"
        ):
            return

        tokenizer = self.models[model_name]["tokenizer"]
        chat_template_info = {
            "has_template": False,
            "template": None,
            "format_type": "generic",
            "special_tokens": {},
            "template_name": None,
        }

        try:
            from utils.datasets import MODEL_TO_TEMPLATE_MAPPER

            # Try exact match first
            model_name_lower = model_name.lower()
            if model_name_lower in MODEL_TO_TEMPLATE_MAPPER:
                chat_template_info["template_name"] = MODEL_TO_TEMPLATE_MAPPER[
                    model_name_lower
                ]
                logger.info(
                    f"Detected template '{chat_template_info['template_name']}' for {model_name} from mapper"
                )
            else:
                # Try partial match (for variants like model_name-bnb-4bit)
                for key in MODEL_TO_TEMPLATE_MAPPER:
                    if key in model_name_lower or model_name_lower in key:
                        chat_template_info["template_name"] = MODEL_TO_TEMPLATE_MAPPER[
                            key
                        ]
                        logger.info(
                            f"Detected template '{chat_template_info['template_name']}' for {model_name} (partial match)"
                        )
                        break
        except Exception as e:
            logger.warning(
                f"Could not detect template from mapper for {model_name}: {e}"
            )

        try:
            if hasattr(tokenizer, "chat_template") and tokenizer.chat_template:
                chat_template_info["has_template"] = True
                chat_template_info["template"] = tokenizer.chat_template

                template_str = tokenizer.chat_template.lower()

                if (
                    "start_header_id" in template_str
                    and "end_header_id" in template_str
                ):
                    chat_template_info["format_type"] = "llama3"
                elif "[inst]" in template_str and "[/inst]" in template_str:
                    chat_template_info["format_type"] = "mistral"
                elif "<|im_start|>" in template_str and "<|im_end|>" in template_str:
                    chat_template_info["format_type"] = "chatml"
                elif "### instruction:" in template_str or "### human:" in template_str:
                    chat_template_info["format_type"] = "alpaca"
                else:
                    chat_template_info["format_type"] = "custom"

                logger.info(
                    f"Loaded chat template for {model_name} (detected as {chat_template_info['format_type']} format)"
                )
                logger.debug(f"Template preview: {tokenizer.chat_template[:200]}...")

                special_tokens = {}
                if hasattr(tokenizer, "bos_token") and tokenizer.bos_token:
                    special_tokens["bos_token"] = tokenizer.bos_token
                if hasattr(tokenizer, "eos_token") and tokenizer.eos_token:
                    special_tokens["eos_token"] = tokenizer.eos_token
                if hasattr(tokenizer, "pad_token") and tokenizer.pad_token:
                    special_tokens["pad_token"] = tokenizer.pad_token

                chat_template_info["special_tokens"] = special_tokens

            else:
                logger.info(
                    f"No chat template found for {model_name}, will use generic formatting"
                )

        except Exception as e:
            logger.error(f"Error loading chat template info for {model_name}: {e}")

        self.models[model_name]["chat_template_info"] = chat_template_info

        if chat_template_info["has_template"]:
            logger.info(
                f"Chat template loaded for {model_name}: {chat_template_info['format_type']} format"
            )
        else:
            logger.info(
                f"No built-in chat template for {model_name}, will use generic formatting"
            )