async def test_listen_for_quit_command():
            if sys.platform == "win32":
                while True:
                    try:
                        if mock_kbhit():
                            raw = mock_getch()
                            try:
                                key = raw.decode("utf-8")
                            except UnicodeDecodeError:
                                continue

                            if len(key) != 1 or not key.isprintable():
                                continue

                            if key.lower() == "q":
                                user_done_event.set()
                                return

                        await asyncio.sleep(0.1)
                    except Exception as e:
                        continue