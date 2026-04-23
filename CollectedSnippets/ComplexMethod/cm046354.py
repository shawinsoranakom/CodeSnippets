def wrapper(*args, **kwargs):
            """Set rc parameters and backend, call the original function, and restore the settings."""
            import matplotlib.pyplot as plt  # scope for faster 'import ultralytics'

            # Prepend Arial Unicode for non-Latin text (CJK, Arabic, etc.); matplotlib falls back if missing
            if "font.sans-serif" not in rcparams and not wrapper._fonts_registered:
                from matplotlib import font_manager

                # Register any fonts in Ultralytics config dir (e.g. Arial.Unicode.ttf) with matplotlib
                known = {f.fname for f in font_manager.fontManager.ttflist}
                for f in USER_CONFIG_DIR.glob("*.ttf"):
                    if str(f) not in known:
                        font_manager.fontManager.addfont(str(f))
                wrapper._fonts_registered = True
            rc = (
                rcparams
                if "font.sans-serif" in rcparams
                else {**rcparams, "font.sans-serif": ["Arial Unicode MS", *plt.rcParams.get("font.sans-serif", [])]}
            )

            original_backend = plt.get_backend()
            switch = backend.lower() != original_backend.lower()
            if switch:
                plt.close("all")  # auto-close()ing of figures upon backend switching is deprecated since 3.8
                plt.switch_backend(backend)

            # Plot with backend and always revert to original backend
            try:
                with plt.rc_context(rc):
                    result = func(*args, **kwargs)
            finally:
                if switch:
                    plt.close("all")
                    plt.switch_backend(original_backend)
            return result