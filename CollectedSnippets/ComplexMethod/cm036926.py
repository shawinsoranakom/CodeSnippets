async def test_customer_middleware_with_vllm_server(self):
        """Test that customer middlewares work with actual vLLM server.

        Tests decorator-based middlewares (@custom_middleware, @input_formatter,
        @output_formatter)
        on multiple endpoints (chat/completions, invocations).
        """
        try:
            from model_hosting_container_standards.sagemaker.config import (
                SageMakerEnvVars,
            )
        except ImportError:
            pytest.skip("model-hosting-container-standards not available")

        # Customer writes a middleware script with multiple decorators
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
from model_hosting_container_standards.common.fastapi.middleware import (
    custom_middleware, input_formatter, output_formatter
)

# Global flag to track if input formatter was called
_input_formatter_called = False

@input_formatter
async def customer_input_formatter(request):
    # Process input - mark that input formatter was called
    global _input_formatter_called
    _input_formatter_called = True
    return request

@custom_middleware("throttle")
async def customer_throttle_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Customer-Throttle"] = "applied"
    order = response.headers.get("X-Middleware-Order", "")
    response.headers["X-Middleware-Order"] = order + "throttle,"
    return response

@output_formatter
async def customer_output_formatter(response):
    global _input_formatter_called
    response.headers["X-Customer-Processed"] = "true"
    # Since input_formatter and output_formatter are combined into
    # pre_post_process middleware,
    # if output_formatter is called, input_formatter should have been called too
    if _input_formatter_called:
        response.headers["X-Input-Formatter-Called"] = "true"
    order = response.headers.get("X-Middleware-Order", "")
    response.headers["X-Middleware-Order"] = order + "output_formatter,"
    return response
"""
            )
            script_path = f.name

        try:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)

            # Set environment variables to point to customer script
            env_vars = {
                SageMakerEnvVars.SAGEMAKER_MODEL_PATH: script_dir,
                SageMakerEnvVars.CUSTOM_SCRIPT_FILENAME: script_name,
            }

            args = [
                "--dtype",
                "bfloat16",
                "--max-model-len",
                "2048",
                "--enforce-eager",
                "--max-num-seqs",
                "32",
            ]

            with RemoteOpenAIServer(
                MODEL_NAME_SMOLLM, args, env_dict=env_vars
            ) as server:
                # Test 1: Middlewares applied to chat/completions endpoint
                chat_response = requests.post(
                    server.url_for("v1/chat/completions"),
                    json={
                        "model": MODEL_NAME_SMOLLM,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 5,
                        "temperature": 0.0,
                    },
                )

                assert chat_response.status_code == 200

                # Verify all middlewares were executed
                assert "X-Customer-Throttle" in chat_response.headers
                assert chat_response.headers["X-Customer-Throttle"] == "applied"
                assert "X-Customer-Processed" in chat_response.headers
                assert chat_response.headers["X-Customer-Processed"] == "true"

                # Verify input formatter was called
                assert "X-Input-Formatter-Called" in chat_response.headers
                assert chat_response.headers["X-Input-Formatter-Called"] == "true"

                # Verify middleware execution order
                execution_order = chat_response.headers.get(
                    "X-Middleware-Order", ""
                ).rstrip(",")
                order_parts = execution_order.split(",") if execution_order else []
                assert "throttle" in order_parts
                assert "output_formatter" in order_parts

                # Test 2: Middlewares applied to invocations endpoint
                invocations_response = requests.post(
                    server.url_for("invocations"),
                    json={
                        "model": MODEL_NAME_SMOLLM,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 5,
                        "temperature": 0.0,
                    },
                )

                assert invocations_response.status_code == 200

                # Verify all middlewares were executed
                assert "X-Customer-Throttle" in invocations_response.headers
                assert invocations_response.headers["X-Customer-Throttle"] == "applied"
                assert "X-Customer-Processed" in invocations_response.headers
                assert invocations_response.headers["X-Customer-Processed"] == "true"

                # Verify input formatter was called
                assert "X-Input-Formatter-Called" in invocations_response.headers
                assert (
                    invocations_response.headers["X-Input-Formatter-Called"] == "true"
                )

        finally:
            os.unlink(script_path)