def read_single_conf_with_lru_cache(arg):
    from shared_utils.key_pattern_manager import is_any_api_key
    try:
        # 优先级1. 获取环境变量作为配置
        default_ref = getattr(importlib.import_module('config'), arg) # 读取默认值作为数据类型转换的参考
        r = read_env_variable(arg, default_ref)
    except:
        try:
            # 优先级2. 获取config_private中的配置
            r = getattr(importlib.import_module('config_private'), arg)
        except:
            # 优先级3. 获取config中的配置
            r = getattr(importlib.import_module('config'), arg)

    # 在读取API_KEY时，检查一下是不是忘了改config
    if arg == 'API_URL_REDIRECT':
        oai_rd = r.get("https://api.openai.com/v1/chat/completions", None) # API_URL_REDIRECT填写格式是错误的，请阅读`https://github.com/binary-husky/gpt_academic/wiki/项目配置说明`
        if oai_rd and not oai_rd.endswith('/completions'):
            log亮红("\n\n[API_URL_REDIRECT] API_URL_REDIRECT填错了。请阅读`https://github.com/binary-husky/gpt_academic/wiki/项目配置说明`。如果您确信自己没填错，无视此消息即可。")
            time.sleep(5)
    if arg == 'API_KEY':
        log亮蓝(f"[API_KEY] 本项目现已支持OpenAI和Azure的api-key。也支持同时填写多个api-key，如API_KEY=\"openai-key1,openai-key2,azure-key3\"")
        log亮蓝(f"[API_KEY] 您既可以在config.py中修改api-key(s)，也可以在问题输入区输入临时的api-key(s)，然后回车键提交后即可生效。")
        if is_any_api_key(r):
            log亮绿(f"[API_KEY] 您的 API_KEY 是: {r[:15]}*** API_KEY 导入成功")
        else:
            log亮红(f"[API_KEY] 您的 API_KEY（{r[:15]}***）不满足任何一种已知的密钥格式，请在config文件中修改API密钥之后再运行（详见`https://github.com/binary-husky/gpt_academic/wiki/api_key`）。")
    if arg == 'proxies':
        if not read_single_conf_with_lru_cache('USE_PROXY'): r = None # 检查USE_PROXY，防止proxies单独起作用
        if r is None:
            log亮红('[PROXY] 网络代理状态：未配置。无代理状态下很可能无法访问OpenAI家族的模型。建议：检查USE_PROXY选项是否修改。')
        else:
            log亮绿('[PROXY] 网络代理状态：已配置。配置信息如下：', str(r))
            assert isinstance(r, dict), 'proxies格式错误，请注意proxies选项的格式，不要遗漏括号。'
    return r