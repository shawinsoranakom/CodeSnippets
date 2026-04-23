def seeded_user_credentials(base_url: str, login_url: str, browser) -> tuple[str, str]:
    _sync_seeded_credentials_from_admin_env()
    env_email = os.getenv("SEEDED_USER_EMAIL")
    env_password = os.getenv("SEEDED_USER_PASSWORD")
    if env_email and env_password:
        return env_email, env_password

    seeding_mode = os.getenv("RAGFLOW_SEEDING_MODE", "auto").strip().lower()
    if seeding_mode not in {"auto", "api", "ui"}:
        if _env_bool("PW_FIXTURE_DEBUG", False):
            print(
                f"[seeded] Unknown RAGFLOW_SEEDING_MODE={seeding_mode!r}; using auto.",
                flush=True,
            )
        seeding_mode = "auto"

    base_email = os.getenv("REG_EMAIL_BASE", REG_EMAIL_BASE_DEFAULT)
    password = os.getenv("SEEDED_USER_PASSWORD") or REG_PASSWORD_DEFAULT
    nickname = os.getenv("REG_NICKNAME", REG_NICKNAME_DEFAULT)
    email = _generate_seeded_email(base_email)
    _assert_reg_email(email)

    seed_errors = []
    seeded_via = None
    if seeding_mode in {"auto", "api"}:
        seeded_via = "api"
        try:
            _api_register_user(base_url, email, password, nickname)
            try:
                _api_login_user(base_url, email, password)
            except Exception as exc:
                if _env_bool("PW_FIXTURE_DEBUG", False):
                    print(f"[seeded] api login verification failed: {exc}", flush=True)
        except _RegisterDisabled as exc:
            seed_errors.append(f"api: {exc}")
            seeded_via = None
        except Exception as exc:
            seed_errors.append(f"api: {exc}")
            seeded_via = None
            if seeding_mode == "api":
                details = "; ".join(seed_errors)
                raise RuntimeError(
                    f"Failed to seed user via API registration. {details}"
                ) from exc

    if seeded_via is None and seeding_mode in {"auto", "ui"}:
        seeded_via = "ui"
        try:
            _ui_register_user(browser, login_url, email, password, nickname)
        except _RegisterDisabled as exc:
            seed_errors.append(f"ui: {exc}")
            default_email = os.getenv("DEFAULT_SUPERUSER_EMAIL", "admin@ragflow.io")
            raise RuntimeError(
                "User registration is disabled and no default account is available. "
                f"Known superuser defaults ({default_email}) cannot be used with the "
                "normal login endpoint. Enable registration or seed a test account."
            ) from exc
        except Exception as ui_exc:
            seed_errors.append(f"ui: {ui_exc}")
            details = "; ".join(seed_errors)
            raise RuntimeError(
                f"Failed to seed user via API or UI registration. {details}"
            ) from ui_exc

    os.environ["SEEDED_USER_EMAIL"] = email
    os.environ["SEEDED_USER_PASSWORD"] = password
    if _env_bool("PW_FIXTURE_DEBUG", False):
        print(f"[seeded] created user via {seeded_via}: {email}", flush=True)
    return email, password