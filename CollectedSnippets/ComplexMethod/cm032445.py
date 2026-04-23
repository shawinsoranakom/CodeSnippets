def _describe_auth_ui(page, card, register_toggle) -> str:
    lines = []
    if card is None:
        lines.append("auth_card_count=unavailable")
    else:
        try:
            lines.append(f"auth_card_count={card.count()}")
        except Exception as exc:
            lines.append(f"auth_card_count_error={exc}")
    if register_toggle is None:
        lines.append("register_toggle_count=unavailable")
    else:
        try:
            toggle_count = register_toggle.count()
            toggle_visible = False
            if toggle_count:
                try:
                    toggle_visible = register_toggle.first.is_visible()
                except Exception:
                    toggle_visible = False
            lines.append(f"register_toggle_count={toggle_count}")
            lines.append(f"register_toggle_visible={toggle_visible}")
        except Exception as exc:
            lines.append(f"register_toggle_error={exc}")
    try:
        summary = _auth_ready_summary(page)
        lines.append(_format_auth_ready_summary(summary).strip())
    except Exception as exc:
        lines.append(f"auth_summary_error={exc}")
    return "\n".join(line for line in lines if line)