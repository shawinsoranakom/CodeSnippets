def _ensure_auth(client: HttpClient, args: argparse.Namespace) -> None:
    if args.api_key:
        client.api_key = args.api_key
        return
    if not args.login_email:
        raise AuthError("Missing API key and login email")
    if not args.login_password:
        raise AuthError("Missing login password")

    password_enc = auth.encrypt_password(args.login_password)

    if args.allow_register:
        nickname = args.login_nickname or args.login_email.split("@")[0]
        try:
            auth.register_user(client, args.login_email, nickname, password_enc)
        except AuthError as exc:
            eprint(f"Register warning: {exc}")

    login_token = auth.login_user(client, args.login_email, password_enc)
    client.login_token = login_token

    if args.bootstrap_llm:
        if not args.llm_factory:
            raise AuthError("Missing --llm-factory for bootstrap")
        if not args.llm_api_key:
            raise AuthError("Missing --llm-api-key for bootstrap")
        existing = auth.get_my_llms(client)
        if args.llm_factory not in existing:
            auth.set_llm_api_key(client, args.llm_factory, args.llm_api_key, args.llm_api_base)

    if args.set_tenant_info:
        if not args.tenant_llm_id or not args.tenant_embd_id:
            raise AuthError("Missing --tenant-llm-id or --tenant-embd-id for tenant setup")
        tenant = auth.get_tenant_info(client)
        tenant_id = tenant.get("tenant_id")
        if not tenant_id:
            raise AuthError("Tenant info missing tenant_id")
        payload = {
            "tenant_id": tenant_id,
            "llm_id": args.tenant_llm_id,
            "embd_id": args.tenant_embd_id,
            "img2txt_id": args.tenant_img2txt_id or "",
            "asr_id": args.tenant_asr_id or "",
            "tts_id": args.tenant_tts_id,
        }
        auth.set_tenant_info(client, payload)

    api_key = auth.create_api_token(client, login_token, args.token_name)
    client.api_key = api_key