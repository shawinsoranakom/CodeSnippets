def test_port_lock_basic_functionality(self):
        """Test basic port lock functionality."""
        port = 30001

        # Test acquiring and releasing a lock
        lock1 = PortLock(port)
        assert lock1.acquire(timeout=1.0)
        assert lock1.is_locked

        # Test that another lock cannot acquire the same port
        lock2 = PortLock(port)
        assert not lock2.acquire(timeout=0.1)
        assert not lock2.is_locked

        # Release first lock
        lock1.release()
        assert not lock1.is_locked

        # Now second lock should be able to acquire
        assert lock2.acquire(timeout=1.0)
        assert lock2.is_locked

        lock2.release()