async def test_middleware_env_var_override(self):
        """Test middleware environment variable overrides."""
        try:
            from model_hosting_container_standards.common.fastapi.config import (
                FastAPIEnvVars,
            )
            from model_hosting_container_standards.sagemaker.config import (
                SageMakerEnvVars,
            )
        except ImportError:
            pytest.skip("model-hosting-container-standards not available")

        # Create a script with middleware functions specified via env vars
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
from fastapi import Request

# Global flag to track if pre_process was called
_pre_process_called = False

async def env_throttle_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Env-Throttle"] = "applied"
    return response

async def env_pre_process(request: Request) -> Request:
    # Mark that pre_process was called
    global _pre_process_called
    _pre_process_called = True
    return request

async def env_post_process(response):
    global _pre_process_called
    if hasattr(response, 'headers'):
        response.headers["X-Env-Post-Process"] = "applied"
        # Since pre_process and post_process are combined into
        # pre_post_process middleware,
        # if post_process is called, pre_process should have been called too
        if _pre_process_called:
            response.headers["X-Pre-Process-Called"] = "true"
    return response
"""
            )
            script_path = f.name

        try:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)

            # Set environment variables for middleware
            # Use script_name with .py extension as per plugin example
            env_vars = {
                SageMakerEnvVars.SAGEMAKER_MODEL_PATH: script_dir,
                SageMakerEnvVars.CUSTOM_SCRIPT_FILENAME: script_name,
                FastAPIEnvVars.CUSTOM_FASTAPI_MIDDLEWARE_THROTTLE: (
                    f"{script_name}:env_throttle_middleware"
                ),
                FastAPIEnvVars.CUSTOM_PRE_PROCESS: f"{script_name}:env_pre_process",
                FastAPIEnvVars.CUSTOM_POST_PROCESS: f"{script_name}:env_post_process",
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
                response = requests.get(server.url_for("ping"))
                assert response.status_code == 200

                # Check if environment variable middleware was applied
                headers = response.headers

                # Verify that env var middlewares were applied
                assert "X-Env-Throttle" in headers, (
                    "Throttle middleware should be applied via env var"
                )
                assert headers["X-Env-Throttle"] == "applied"

                assert "X-Env-Post-Process" in headers, (
                    "Post-process middleware should be applied via env var"
                )
                assert headers["X-Env-Post-Process"] == "applied"

                # Verify that pre_process was called
                assert "X-Pre-Process-Called" in headers, (
                    "Pre-process should be called via env var"
                )
                assert headers["X-Pre-Process-Called"] == "true"

        finally:
            os.unlink(script_path)