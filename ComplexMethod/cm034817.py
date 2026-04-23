def oauth_login(provider: str):
            timeout = 300.0
            if request.method == 'GET':
                timeout = float(request.args.get('timeout') or timeout)
            else:
                try:
                    data = request.get_json(silent=True) or {}
                    timeout = float(data.get('timeout') or timeout)
                except Exception:
                    pass

            # Resolve provider class
            try:
                provider_class = ProviderUtils.get_by_label(provider)
            except ValueError as e:
                return jsonify({"error": {"message": str(e)}}), 404

            if request.method == 'GET':
                data = request.args.to_dict() or {}
            else:
                data = request.get_json(silent=True) or {}

            action = data.get("action", "start")

            # Github Copilot device flow: start/poll actions
            if hasattr(provider_class, "oauth_start") and action == "start":
                try:
                    result = asyncio.run(provider_class.oauth_start())
                    return jsonify(result), 200
                except Exception as e:
                    logger.exception(e)
                    return jsonify({"error": {"message": str(e)}}), 500

            if hasattr(provider_class, "oauth_poll") and action == "poll":
                device_code = data.get("device_code")
                if not device_code:
                    return jsonify({"error": {"message": "device_code is required for poll action"}}), 400
                try:
                    result = asyncio.run(provider_class.oauth_poll(device_code))
                    return jsonify(result), 200
                except Exception as e:
                    logger.exception(e)
                    return jsonify({"error": {"message": str(e)}}), 500

            # Fallback: provider.login (blocking) for interactive login flows
            if hasattr(provider_class, "login"):
                try:
                    asyncio.run(provider_class.login())
                    return jsonify({"status": "success"}), 200
                except Exception as e:
                    logger.exception(e)
                    return jsonify({"error": {"message": str(e)}}), 500

            return jsonify({"error": {"message": f"Provider {provider} does not support OAuth login"}}), 404