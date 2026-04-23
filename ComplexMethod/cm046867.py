def construct_chat_template( \

tokenizer = None,

chat_template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{SYSTEM}<|eot_id|><|start_header_id|>user<|end_header_id|>

{INPUT}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{OUTPUT}<|eot_id|><|start_header_id|>user<|end_header_id|>

{INPUT}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{OUTPUT}<|eot_id|>""",

default_system_message = \
    "Below are some instructions that describe some tasks. Write responses that appropriately complete each request.",

extra_eos_tokens = None,
):
    """
    Creates an Ollama modelfile and a HF Jinja template from a custom
    template. You must provide 2x examples of an input & output.
    There is an optional system message as well.

    You must use {INPUT}, {OUTPUT} twice, and {SYSTEM} is optional.
    """
    # Strip only the left
    chat_template = chat_template.lstrip()

    assert(tokenizer is not None)

    if extra_eos_tokens is None: extra_eos_tokens = []
    elif type(extra_eos_tokens) is str: extra_eos_tokens = [extra_eos_tokens,]

    vocab = tokenizer.get_vocab()
    for extra_eos in extra_eos_tokens:
        assert(type(extra_eos) is str)
        if extra_eos not in vocab:
            raise ValueError(f"Unsloth: `{extra_eos}` is not a singular token in the tokenizer.")

    error_msg = \
        "Unsloth: Your prompt template must have 2 examples showing the user input {INPUT} "\
        "and the assistant output {OUTPUT}\n\n"\
        "For example what is not allowed is just:\n"\
        "### Input:\\n{INPUT}\\n\\n### Response:\\n{OUTPUT}\\n\n\n"\
        "What is required is 2x of this:\n"\
        "### Input:\\n{INPUT}\\n\\n### Response:\\n{OUTPUT}\\n"\
        "### Input:\\n{INPUT}\\n\\n### Response:\\n{OUTPUT}\\n"

    # Check for EOS after {OUTPUT}
    if tokenizer.eos_token is not None:
        extra_eos_tokens.insert(0, tokenizer.eos_token)
    if len(extra_eos_tokens) == 0:
        raise RuntimeError(
            "Unsloth: Your tokenizer does not have an EOS token? Please provide one via extra_eos_tokens!"
        )

    # Check tokenizer types
    tokenizer_name = tokenizer.name_or_path.lower()
    if tokenizer_name.startswith(("unsloth/llama-3-8b-instruct", "unsloth/llama-3-70b-instruct")):
        # Add <|eot_id|>
        extra_eos_tokens.append("<|eot_id|>")
    elif ("<|eot_id|>" in extra_eos_tokens or "<|eot_id|>" in chat_template) and \
        tokenizer_name.startswith(("unsloth/llama-3-8b", "unsloth/llama-3-70b")):
        # Warn
        logger.warning(
            "Unsloth: Base llama-3 models did not train <|eot_id|>.\n"\
            "Please use the instruct version or use <|end_of_text|>"
        )
    extra_eos_tokens = list(set(extra_eos_tokens))

    count_eos = 0
    for eos in extra_eos_tokens:
        count_eos += len(re.findall(r"{OUTPUT}" + re.escape(eos), chat_template))

    # This forces you to provide 2 input and outputs
    final_combined_check = False

    try:
        # O(N^2) search finding 2 repeatted pieces of text
        j = len(chat_template)-1
        at_least_one = False
        while j > 0:
            found = chat_template.rfind(chat_template[j:], 0, j)
            if found == -1: break
            j -= 1
            at_least_one = True
        if j > 0: j += 1
        else: raise RuntimeError(error_msg)

        if not at_least_one: raise RuntimeError(error_msg)

        # Must be equivalent to left
        final_combined_check = True

        # Repeatted text
        instruction_response = chat_template[j:]
        if instruction_response.count("{INPUT}") != 1 or instruction_response.count("{OUTPUT}") != 1:
            raise RuntimeError(error_msg)

        # 1st System, Instruction, Output pair
        left  = chat_template[:j]
        # 2nd Instruction, Output pair
        right = chat_template[j:]

        final_combined_check = left if final_combined_check else chat_template

        # Isolate input
        extra_eos_tokens_regex = "|".join(f"(?:{re.escape(x)})" for x in extra_eos_tokens)
        if len(extra_eos_tokens_regex) != 0:
            find_end = f"(?:{extra_eos_tokens_regex})?"
        else:
            find_end = ""
        find_end = r"\{INPUT\}[\s\n]{0,}" + find_end
        input_end = list(re.finditer(find_end, right))
        assert(len(input_end) == 1)
        input_end = input_end[0]
        input_end = input_end.span(0)[1]
        input_part = right[:input_end]

        # Isolate output
        output_part = right[input_end:]

        # Isolate system
        where_system = left.find(input_part)
        system_part = left[:where_system if where_system != -1 else len(left)]

        # Check if the user provided a correct prompt
        combined = system_part + input_part + output_part
        if combined != final_combined_check:
            combined_changed = combined            .replace('\n', '\\n')
            left_changed     = final_combined_check.replace('\n', '\\n')
            raise RuntimeError(
                "Unsloth: The prompt template you provided isn't correct. You gave:\n"\
                f"{combined_changed}\n\n"\
                "But we require the following:\n"\
                f"{left_changed}"
            )
    except:
        ending = chat_template[chat_template.find("{OUTPUT}") + len("{OUTPUT}"):]

        ending = re.escape(ending)
        find_text = "{INPUT}" + ending + "(.+?{OUTPUT}" + ending + ")"
        response_part = re.findall(find_text, chat_template, flags = re.DOTALL | re.MULTILINE)
        response_part = response_part[0]

        for j in range(1, len(response_part)):
            try_find = re.escape(response_part[:j])
            try: found = next(re.finditer("(" + try_find + ").+?\\{INPUT\\}", chat_template, flags = re.DOTALL | re.MULTILINE))
            except: break
        separator = found.group(1)

        response_start = chat_template.find(response_part)
        start_instruction = chat_template[:response_start].rfind(separator)
        if start_instruction == -1: start_instruction = 0
        instruction_part = chat_template[start_instruction:response_start]

        combined = instruction_part + response_part
        where = chat_template.find(combined)
        system_part = chat_template[:where]

        system_part, input_part, output_part = system_part, instruction_part, response_part

    if count_eos == 0:
        logger.warning("Unsloth: We automatically added an EOS token to stop endless generations.")
        eos = extra_eos_tokens[0]
        output_part = output_part + eos

    # Ollama modelfile parts

    # Check bos_token is in system prompt
    ollama_system = system_part
    has_bos_token = False
    always_bos_token = False
    if tokenizer("A").input_ids[0] == getattr(tokenizer, "bos_token_id", None):
        always_bos_token = True
        if ollama_system.startswith(tokenizer.bos_token):
            has_bos_token = True
            ollama_system = ollama_system[len(tokenizer.bos_token):]
    # Check system
    if "{SYSTEM}" in ollama_system:
        system_modelfile = "{{ if .System }}" + ollama_system.replace("{SYSTEM}", "{{ .System }}") + "{{ end }}"
    else:
        system_modelfile = ollama_system
    input_modelfile  = "{{ if .Prompt }}" + input_part .replace("{INPUT}",  "{{ .Prompt }}") + "{{ end }}"
    output_modelfile = output_part.replace("{OUTPUT}", "{{ .Response }}")

    # Ollama EOS
    ollama_eos = get_ollama_eos_tokens(tokenizer, extra_eos_tokens)
    ollama_eos = '\n'.join(f'PARAMETER stop "{eos}"' for eos in ollama_eos)

    # Add temperature and min_p to counteract gibberish
    ollama_eos += "\nPARAMETER temperature 1.5\nPARAMETER min_p 0.1"

    # Ollama modelfile
    part = '"""'
    modelfile = 'FROM {__FILE_LOCATION__}\n\n'\
    'TEMPLATE ' + part + system_modelfile + input_modelfile + output_modelfile + \
        part + '\n\n' + ollama_eos

    # HF Jinja Chat template
    def process(part, which, content = "message['content']"):
        if part.endswith(which):
            part = "'" + part[:part.find(which)] + f"' + {content}"
        elif part.startswith(which):
            part = f"{content} + '" + part[part.find(which):] + "'"
        else:
            part = "'" + part.replace(which, f"' + {content} + '") + "'"
        if part.startswith("'' + "): part = part[5:]
        return part
    input_jinja  = process(input_part,  "{INPUT}")
    output_jinja = process(output_part, "{OUTPUT}")

    jinja_template = \
        "{% for message in loop_messages %}"\
            "{% if message['role'] == 'user' %}"\
                "{{ " + input_jinja + " }}"\
            "{% elif message['role'] == 'assistant' %}"\
                "{{ " + output_jinja + " }}"\
            "{% else %}"\
                "{{ raise_exception('Only user and assistant roles are supported!') }}"\
            "{% endif %}"\
        "{% endfor %}"\
        "{% if add_generation_prompt %}"\
            "{{ '" + output_part[:output_part.find("{OUTPUT}")] + "' }}"\
        "{% endif %}"

    # Now add system prompt to jinja
    if len(system_part) != 0:
        partial_system = process(system_part, "{SYSTEM}", "messages[0]['content']")
        partial_system = partial_system.replace("{SYSTEM}", "")

        if "{SYSTEM}" in partial_system:
            if default_system_message is None:
                raise RuntimeError("Unsloth: Please specify a default system message!")

        # Separate the BOS
        if has_bos_token:
            partial_system = partial_system.replace(tokenizer.bos_token, "", 1)
            system_part    = system_part   .replace(tokenizer.bos_token, "", 1)

        partial_system = \
            "{% if messages[0]['role'] == 'system' %}"\
                "{{ " + partial_system + " }}"\
                "{% set loop_messages = messages[1:] %}"
        if default_system_message is not None:
            full_system = system_part.replace("{SYSTEM}", default_system_message)
            if "{SYSTEM}" in system_part:
                modelfile += '\nSYSTEM "' + default_system_message + '"'
            partial_system += "{% else %}"\
                "{{ '" + full_system + "' }}"\
                "{% set loop_messages = messages %}"\
            "{% endif %}"
        else:
            partial_system += "{% endif %}"

        jinja_template = partial_system + jinja_template

        if has_bos_token:
            jinja_template = "{{ bos_token }}" + jinja_template

    # Fix missing loop_messages
    if "{% set loop_messages = messages %}" not in jinja_template:
        jinja_template = jinja_template.replace(
            "{% for message in loop_messages %}",
            "{% for message in messages %}",
            1, # Only replace the first one
        )

    # Check if system part is the same!
    jinja_template = re.sub(
        r"\{\% if messages\[0\]\['role'\] \=\= 'system' \%\}\{\{ '(.+?)' \}\}"\
        r"\{\% set loop\_messages \= messages\[1\:\] \%\}"\
        r"\{\% else \%\}\{\{ '\1' \}\}\{\% set loop\_messages \= messages \%\}\{\% endif \%\}"\
        r"\{\% for message in loop\_messages \%\}",
        r"{{ '\1' }}{% for message in messages %}",
        jinja_template, flags = re.MULTILINE | re.DOTALL,
    )

    # Check jinja template for bos
    if always_bos_token:
        if not jinja_template.startswith(("{{ bos_token }}", "{{- bos_token }}")):
            jinja_template = "{{ bos_token }}" + jinja_template

    # Get instruction and output parts for train_on_inputs = False
    input_part  = input_part [:input_part .find("{INPUT}")]
    output_part = output_part[:output_part.find("{OUTPUT}")]
    return modelfile, jinja_template, input_part, output_part