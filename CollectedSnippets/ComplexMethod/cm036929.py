async def test_tokenize_chat(
    server: RemoteOpenAIServer,
    model_name: str,
    tokenizer_name: str,
):
    tokenizer = get_tokenizer(tokenizer_name=tokenizer_name)

    for add_generation in [False, True]:
        for add_special in [False, True]:
            conversation = [
                {"role": "user", "content": "Hi there!"},
                {"role": "assistant", "content": "Nice to meet you!"},
                {"role": "user", "content": "Can I ask a question? vllm1"},
            ]
            for continue_final in [False, True]:
                if add_generation and continue_final:
                    continue
                if continue_final:
                    conversation.append({"role": "assistant", "content": "Sure,"})

                prompt = tokenizer.apply_chat_template(
                    add_generation_prompt=add_generation,
                    continue_final_message=continue_final,
                    conversation=conversation,
                    tokenize=False,
                )
                tokens = tokenizer.encode(prompt, add_special_tokens=add_special)

                response = requests.post(
                    server.url_for("tokenize"),
                    json={
                        "add_generation_prompt": add_generation,
                        "continue_final_message": continue_final,
                        "add_special_tokens": add_special,
                        "messages": conversation,
                        "model": model_name,
                    },
                )
                response.raise_for_status()

                result = response.json()
                assert result["tokens"] == tokens
                assert result["count"] == len(tokens)
                assert result["max_model_len"] == 8192
                assert result["token_strs"] is None