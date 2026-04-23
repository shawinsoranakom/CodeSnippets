def worker_fn_test_idle_to_busy():
    rank = dist.get_rank()
    writer_rank = 2
    message_queue = MessageQueue.create_from_process_group(
        dist.group.WORLD, 40 * 1024, 2, writer_rank
    )

    message1 = "hello world"
    message2 = np.random.randint(1, 100, 100)
    with mock.patch.object(
        message_queue._spin_condition, "wait", wraps=message_queue._spin_condition.wait
    ) as wrapped_wait:
        if not message_queue._is_writer:
            # Put into idle mode
            message_queue._spin_condition.last_read = 0

            # no messages, so expect a TimeoutError
            with pytest.raises(TimeoutError):
                message_queue.dequeue(timeout=0.01)
            # wait should only be called once while idle
            assert wrapped_wait.call_count == 1

            # sync with the writer and wait for message1
            dist.barrier()
            recv_message = message_queue.dequeue(timeout=5)
            assert recv_message == message1
            # second call to wait, with a message read, this puts in a busy spin
            assert wrapped_wait.call_count == 2

            # sync with the writer and wait for message2
            dist.barrier()
            recv_message = message_queue.dequeue(timeout=1)
            assert np.array_equal(recv_message, message2)
            # in busy mode, we expect wait to have been called multiple times
            assert wrapped_wait.call_count > 3
        else:
            # writer writes two messages in sync with the reader
            dist.barrier()
            # sleep delays the send to ensure reader enters the read loop
            time.sleep(0.1)
            message_queue.enqueue(message1)

            dist.barrier()
            time.sleep(0.1)
            message_queue.enqueue(message2)

    message_queue.shutdown()
    assert message_queue.shutting_down
    print(f"torch distributed passed the test! Rank {rank}")