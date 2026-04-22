def test_function(param1: int, param2: str, param3: float = 0.1) -> str:
            st.markdown("This command should not be tracked")
            return "foo"