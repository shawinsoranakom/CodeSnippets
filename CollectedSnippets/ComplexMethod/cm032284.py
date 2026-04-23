def msg_handle_error(llm_kwargs, chunk_decoded):
    use_ket = llm_kwargs.get('use-key', '')
    api_key_encryption = use_ket[:8] + '****' + use_ket[-5:]
    openai_website = f' 请登录OpenAI查看详情 https://platform.openai.com/signup  api-key: `{api_key_encryption}`'
    error_msg = ''
    if "does not exist" in chunk_decoded:
        error_msg = f"[Local Message] Model {llm_kwargs['llm_model']} does not exist. 模型不存在, 或者您没有获得体验资格."
    elif "Incorrect API key" in chunk_decoded:
        error_msg = f"[Local Message] Incorrect API key. OpenAI以提供了不正确的API_KEY为由, 拒绝服务." + openai_website
    elif "exceeded your current quota" in chunk_decoded:
        error_msg = "[Local Message] You exceeded your current quota. OpenAI以账户额度不足为由, 拒绝服务." + openai_website
    elif "account is not active" in chunk_decoded:
        error_msg = "[Local Message] Your account is not active. OpenAI以账户失效为由, 拒绝服务." + openai_website
    elif "associated with a deactivated account" in chunk_decoded:
        error_msg = "[Local Message] You are associated with a deactivated account. OpenAI以账户失效为由, 拒绝服务." + openai_website
    elif "API key has been deactivated" in chunk_decoded:
        error_msg = "[Local Message] API key has been deactivated. OpenAI以账户失效为由, 拒绝服务." + openai_website
    elif "bad forward key" in chunk_decoded:
        error_msg = "[Local Message] Bad forward key. API2D账户额度不足."
    elif "Not enough point" in chunk_decoded:
        error_msg = "[Local Message] Not enough point. API2D账户点数不足."
    elif 'error' in str(chunk_decoded).lower():
        try:
            error_msg = json.dumps(json.loads(chunk_decoded[:6]), indent=4, ensure_ascii=False)
        except:
            error_msg = chunk_decoded
    return error_msg