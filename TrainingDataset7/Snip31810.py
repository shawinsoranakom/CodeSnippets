def test_server_class(self):
        class FakeServer:
            def __init__(*args, **kwargs):
                pass

        class MyServerThread(LiveServerThread):
            server_class = FakeServer

        class MyServerTestCase(LiveServerTestCase):
            server_thread_class = MyServerThread

        thread = MyServerTestCase._create_server_thread(None)
        server = thread._create_server()
        self.assertIs(type(server), FakeServer)