def test_chat_templates():
    messages = [
        {"role": "system","content": " You are a friendly chatbot.",},
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "It's 4."},
        {"role": "user", "content": "  But 2+2 is equal to 5. "},
        {"role": "assistant", "content": "No I'm sure its 4."},
        {"role": "user", "content": "  No it's 100% 5! "},
    ]

    # Zephyr
    from transformers import AutoTokenizer
    template = zephyr_template
    correct_tokenizer = AutoTokenizer.from_pretrained("HuggingFaceH4/zephyr-7b-beta")
    correct_prompt = correct_tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
    correct_tokenizer.chat_template = template
    our_prompt = correct_tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
    assert(correct_prompt == our_prompt)

    # Chatml
    template = chatml_template
    correct_tokenizer = AutoTokenizer.from_pretrained("teknium/OpenHermes-2.5-Mistral-7B")
    correct_prompt = correct_tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
    correct_tokenizer.chat_template = template
    our_prompt = correct_tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
    assert(correct_prompt == our_prompt)

    # Mistral
    template = mistral_template
    correct_tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
    correct_prompt = correct_tokenizer.apply_chat_template(messages[1:], tokenize = False, add_generation_prompt = True)
    correct_tokenizer.chat_template = template
    our_prompt = correct_tokenizer.apply_chat_template(messages[1:], tokenize = False, add_generation_prompt = True)
    assert(correct_prompt == our_prompt)

    # Llama
    template = llama_template
    correct_tokenizer = AutoTokenizer.from_pretrained("unsloth/llama-2-7b-chat")
    correct_prompt = correct_tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
    correct_tokenizer.chat_template = template
    our_prompt = correct_tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
    assert(correct_prompt == our_prompt)

    # Vicuna
    try:
        from fastchat.conversation import get_conv_template
    except:
        os.system("pip -qqq install git+https://github.com/lm-sys/FastChat.git")
        from fastchat.conversation import get_conv_template
    correct_prompt = get_conv_template("vicuna_v1.1")
    for j in range(len(messages)-1):
        correct_prompt.append_message(correct_prompt.roles[j%2==1], messages[j+1]["content"])
    correct_prompt.append_message(correct_prompt.roles[1], "")
    correct_prompt = tokenizer.bos_token + correct_prompt.get_prompt()

    template = vicuna_template
    correct_tokenizer = AutoTokenizer.from_pretrained("lmsys/vicuna-7b-v1.5")
    correct_tokenizer.chat_template = template
    our_prompt = correct_tokenizer.apply_chat_template(messages[1:], tokenize = False, add_generation_prompt = True)
    assert(correct_prompt == our_prompt)

    try:
        from fastchat.conversation import get_conv_template
    except:
        os.system("pip -qqq install git+https://github.com/lm-sys/FastChat.git")
        from fastchat.conversation import get_conv_template
    correct_prompt = get_conv_template("zero_shot")
    for j in range(len(messages)-1):
        correct_prompt.append_message(correct_prompt.roles[j%2==1], messages[j+1]["content"])
    correct_prompt.append_message(correct_prompt.roles[1], "")
    correct_prompt = tokenizer.bos_token + correct_prompt.get_prompt()

    template = vicuna_old_template
    correct_tokenizer = AutoTokenizer.from_pretrained("lmsys/vicuna-7b-v1.5")
    correct_tokenizer.chat_template = template
    our_prompt = correct_tokenizer.apply_chat_template(messages[1:], tokenize = False, add_generation_prompt = True)
    # We add </s> ourselves
    assert(correct_prompt == our_prompt.replace("</s>", ""))

    # Gemma
    correct_tokenizer = AutoTokenizer.from_pretrained("unsloth/gemma-7b-it")
    correct_prompt = correct_tokenizer.apply_chat_template(messages[1:], tokenize = False, add_generation_prompt = True)
    correct_tokenizer.chat_template = gemma_template
    our_prompt = correct_tokenizer.apply_chat_template(messages[1:], tokenize = False, add_generation_prompt = True)
    assert(our_prompt == correct_prompt)

    # Llama-3
    template = llama3_template
    correct_tokenizer = AutoTokenizer.from_pretrained("unsloth/llama-3-8b-Instruct")
    correct_prompt = correct_tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
    correct_tokenizer.chat_template = template
    our_prompt = correct_tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)
    assert(correct_prompt == our_prompt)

    # Phi-3
    template = phi3_template
    correct_tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
    correct_prompt = correct_tokenizer.apply_chat_template(messages[1:], tokenize = False, add_generation_prompt = True)
    correct_tokenizer.chat_template = template
    our_prompt = correct_tokenizer.apply_chat_template(messages[1:], tokenize = False, add_generation_prompt = True)
    assert(correct_prompt == our_prompt)