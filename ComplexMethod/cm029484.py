async def _run_variant(
        self,
        index: int,
        model: Llm,
        prompt_messages: List[ChatCompletionMessageParam],
    ) -> str:
        try:
            async def send_runner_message(
                type: str,
                value: str | None,
                variant_index: int,
                data: Dict[str, Any] | None,
                event_id: str | None,
            ) -> None:
                await self.send_message(
                    cast(MessageType, type),
                    value,
                    variant_index,
                    data,
                    event_id,
                )

            runner = Agent(
                send_message=send_runner_message,
                variant_index=index,
                openai_api_key=self.openai_api_key,
                openai_base_url=self.openai_base_url,
                anthropic_api_key=self.anthropic_api_key,
                gemini_api_key=self.gemini_api_key,
                should_generate_images=self.should_generate_images,
                initial_file_state=self.file_state,
                option_codes=self.option_codes,
            )
            completion = await runner.run(model, prompt_messages)
            if completion:
                await self.send_message("setCode", completion, index, None, None)
            await self.send_message(
                "variantComplete",
                "Variant generation complete",
                index,
                None,
                None,
            )
            return completion
        except openai.AuthenticationError as e:
            print(f"[VARIANT {index + 1}] OpenAI Authentication failed", e)
            error_message = (
                "Incorrect OpenAI key. Please make sure your OpenAI API key is correct, "
                "or create a new OpenAI API key on your OpenAI dashboard."
                + (
                    " Alternatively, you can purchase code generation credits directly on this website."
                    if IS_PROD
                    else ""
                )
            )
            await self.send_message("variantError", error_message, index, None, None)
            return ""
        except openai.NotFoundError as e:
            print(f"[VARIANT {index + 1}] OpenAI Model not found", e)
            error_message = (
                e.message
                + ". Please make sure you have followed the instructions correctly to obtain "
                "an OpenAI key with GPT vision access: "
                "https://github.com/abi/screenshot-to-code/blob/main/Troubleshooting.md"
                + (
                    " Alternatively, you can purchase code generation credits directly on this website."
                    if IS_PROD
                    else ""
                )
            )
            await self.send_message("variantError", error_message, index, None, None)
            return ""
        except openai.RateLimitError as e:
            print(f"[VARIANT {index + 1}] OpenAI Rate limit exceeded", e)
            error_message = (
                "OpenAI error - 'You exceeded your current quota, please check your plan and billing details.'"
                + (
                    " Alternatively, you can purchase code generation credits directly on this website."
                    if IS_PROD
                    else ""
                )
            )
            await self.send_message("variantError", error_message, index, None, None)
            return ""
        except Exception as e:
            print(f"Error in variant {index + 1}: {e}")
            traceback.print_exception(type(e), e, e.__traceback__)
            await self.send_message("variantError", str(e), index, None, None)
            return ""