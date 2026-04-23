async def _case():
        async with quart_app.test_request_context("/logout", headers={"Cookie": "remember_token=abc"}):
            from quart import session

            session["_user_id"] = "user-1"
            session["_fresh"] = True
            session["_id"] = "session-id"
            session["_remember_seconds"] = 5

            assert apps_module.logout_user() is True
            assert "_user_id" not in session
            assert "_fresh" not in session
            assert "_id" not in session
            assert session.get("_remember") == "clear"
            assert "_remember_seconds" not in session

        async with quart_app.test_request_context("/missing/path"):
            not_found_resp, status = await apps_module.not_found(RuntimeError("missing"))
            assert status == apps_module.RetCode.NOT_FOUND
            payload = await not_found_resp.get_json()
            assert payload["code"] == apps_module.RetCode.NOT_FOUND
            assert payload["error"] == "Not Found"
            assert "Not Found:" in payload["message"]

        async with quart_app.test_request_context("/protected"):
            @apps_module.login_required
            async def _protected():
                return {"ok": True}

            monkeypatch.setattr(apps_module, "current_user", None)
            with pytest.raises(apps_module.QuartAuthUnauthorized) as exc_info:
                await _protected()

            quart_payload, quart_status = await apps_module.unauthorized_quart_auth(exc_info.value)
            assert quart_status == apps_module.RetCode.UNAUTHORIZED
            assert quart_payload["code"] == apps_module.RetCode.UNAUTHORIZED

            werk_payload, werk_status = await apps_module.unauthorized_werkzeug(WerkzeugUnauthorized("Unauthorized 401"))
            assert werk_status == apps_module.RetCode.UNAUTHORIZED
            assert werk_payload["code"] == apps_module.RetCode.UNAUTHORIZED