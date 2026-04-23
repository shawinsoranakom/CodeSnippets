def test_transaction_base_creation(self):
        """Test creating a TransactionBase instance."""
        flow_id = uuid4()
        transaction = TransactionBase(
            vertex_id="test-vertex-123",
            target_id="target-vertex-456",
            inputs={"key": "value"},
            outputs={"result": "success"},
            status="success",
            flow_id=flow_id,
        )

        assert transaction.vertex_id == "test-vertex-123"
        assert transaction.target_id == "target-vertex-456"
        assert transaction.inputs == {"key": "value"}
        assert transaction.outputs == {"result": "success"}
        assert transaction.status == "success"
        assert transaction.flow_id == flow_id
        assert transaction.error is None