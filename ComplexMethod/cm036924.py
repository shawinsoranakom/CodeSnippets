async def test_handler_env_var_override(self):
        """Test CUSTOM_FASTAPI_PING_HANDLER and CUSTOM_FASTAPI_INVOCATION_HANDLER
        environment variable overrides."""
        try:
            from model_hosting_container_standards.common.fastapi.config import (
                FastAPIEnvVars,
            )
            from model_hosting_container_standards.sagemaker.config import (
                SageMakerEnvVars,
            )
        except ImportError:
            pytest.skip("model-hosting-container-standards not available")

        # Create a script with both env var handlers and script functions
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
from fastapi import Request, Response
import json

async def env_var_ping_handler(raw_request: Request) -> Response:
    return Response(
        content=json.dumps({
            "status": "healthy",
            "source": "env_var_ping",
            "method": "environment_variable"
        }),
        media_type="application/json"
    )

async def env_var_invoke_handler(raw_request: Request) -> Response:
    return Response(
        content=json.dumps({
            "predictions": ["Environment variable response"],
            "source": "env_var_invoke",
            "method": "environment_variable"
        }),
        media_type="application/json"
    )

async def custom_sagemaker_ping_handler():
    return {
        "status": "healthy",
        "source": "script_ping",
        "method": "script_function"
    }

async def custom_sagemaker_invocation_handler(request: Request):
    return {
        "predictions": ["Script function response"],
        "source": "script_invoke",
        "method": "script_function"
    }
"""
            )
            script_path = f.name

        try:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)

            # Set environment variables to override both handlers
            env_vars = {
                SageMakerEnvVars.SAGEMAKER_MODEL_PATH: script_dir,
                SageMakerEnvVars.CUSTOM_SCRIPT_FILENAME: script_name,
                FastAPIEnvVars.CUSTOM_FASTAPI_PING_HANDLER: (
                    f"{script_name}:env_var_ping_handler"
                ),
                FastAPIEnvVars.CUSTOM_FASTAPI_INVOCATION_HANDLER: (
                    f"{script_name}:env_var_invoke_handler"
                ),
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
                # Test ping handler override
                ping_response = requests.get(server.url_for("ping"))
                assert ping_response.status_code == 200
                ping_data = ping_response.json()

                # Environment variable should override script function
                assert ping_data["method"] == "environment_variable"
                assert ping_data["source"] == "env_var_ping"

                # Test invocation handler override
                invoke_response = requests.post(
                    server.url_for("invocations"),
                    json={
                        "model": MODEL_NAME_SMOLLM,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 5,
                    },
                )
                assert invoke_response.status_code == 200
                invoke_data = invoke_response.json()

                # Environment variable should override script function
                assert invoke_data["method"] == "environment_variable"
                assert invoke_data["source"] == "env_var_invoke"

        finally:
            os.unlink(script_path)