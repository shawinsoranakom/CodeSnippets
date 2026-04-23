def test_progress_isolation_between_clients(self, args_pytest):
        """Test that progress updates are isolated between different clients."""
        listen = args_pytest["listen"]
        port = args_pytest["port"]

        # Create two separate clients with unique IDs
        client_a_id = "client_a_" + str(uuid.uuid4())
        client_b_id = "client_b_" + str(uuid.uuid4())

        try:
            # Connect both clients with retries
            client_a = self.start_client_with_retry(listen, port, client_a_id)
            client_b = self.start_client_with_retry(listen, port, client_b_id)

            # Create simple workflows for both clients
            graph_a = GraphBuilder(prefix="client_a")
            image_a = graph_a.node("StubImage", content="BLACK", height=256, width=256, batch_size=1)
            graph_a.node("PreviewImage", images=image_a.out(0))

            graph_b = GraphBuilder(prefix="client_b")
            image_b = graph_b.node("StubImage", content="WHITE", height=256, width=256, batch_size=1)
            graph_b.node("PreviewImage", images=image_b.out(0))

            # Submit workflows from both clients
            prompt_a = graph_a.finalize()
            prompt_b = graph_b.finalize()

            response_a = client_a.queue_prompt(prompt_a)
            prompt_id_a = response_a['prompt_id']

            response_b = client_b.queue_prompt(prompt_b)
            prompt_id_b = response_b['prompt_id']

            # Start threads to listen for messages on both clients
            def listen_client_a():
                client_a.listen_for_messages(duration=10.0)

            def listen_client_b():
                client_b.listen_for_messages(duration=10.0)

            thread_a = threading.Thread(target=listen_client_a)
            thread_b = threading.Thread(target=listen_client_b)

            thread_a.start()
            thread_b.start()

            # Wait for threads to complete
            thread_a.join()
            thread_b.join()

            # Verify isolation
            # Client A should only receive progress for prompt_id_a
            assert not client_a.progress_tracker.has_cross_contamination(prompt_id_a), \
                f"Client A received progress updates for other clients' workflows. " \
                f"Expected only {prompt_id_a}, but got messages for multiple prompts."

            # Client B should only receive progress for prompt_id_b
            assert not client_b.progress_tracker.has_cross_contamination(prompt_id_b), \
                f"Client B received progress updates for other clients' workflows. " \
                f"Expected only {prompt_id_b}, but got messages for multiple prompts."

            # Verify each client received their own progress updates
            client_a_messages = client_a.progress_tracker.get_messages_for_prompt(prompt_id_a)
            client_b_messages = client_b.progress_tracker.get_messages_for_prompt(prompt_id_b)

            assert len(client_a_messages) > 0, \
                "Client A did not receive any progress updates for its own workflow"
            assert len(client_b_messages) > 0, \
                "Client B did not receive any progress updates for its own workflow"

            # Ensure no cross-contamination
            client_a_other = client_a.progress_tracker.get_messages_for_prompt(prompt_id_b)
            client_b_other = client_b.progress_tracker.get_messages_for_prompt(prompt_id_a)

            assert len(client_a_other) == 0, \
                f"Client A incorrectly received {len(client_a_other)} progress updates for Client B's workflow"
            assert len(client_b_other) == 0, \
                f"Client B incorrectly received {len(client_b_other)} progress updates for Client A's workflow"

        finally:
            # Clean up connections
            if hasattr(client_a, 'ws'):
                client_a.ws.close()
            if hasattr(client_b, 'ws'):
                client_b.ws.close()