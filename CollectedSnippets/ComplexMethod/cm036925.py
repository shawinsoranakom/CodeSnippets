async def test_env_var_priority_over_decorator_and_script(self):
        """Test that environment variables have highest priority over decorators
        and script functions for both ping and invocation handlers."""
        try:
            from model_hosting_container_standards.common.fastapi.config import (
                FastAPIEnvVars,
            )
            from model_hosting_container_standards.sagemaker.config import (
                SageMakerEnvVars,
            )
        except ImportError:
            pytest.skip("model-hosting-container-standards not available")

        # Create a script with all three handler types for both ping and invocation
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import model_hosting_container_standards.sagemaker as sagemaker_standards
from fastapi import Request, Response
import json

# Environment variable handlers (highest priority)
async def env_priority_ping(raw_request: Request) -> Response:
    return Response(
        content=json.dumps({
            "status": "healthy",
            "source": "env_var",
            "priority": "environment_variable"
        }),
        media_type="application/json"
    )

async def env_priority_invoke(raw_request: Request) -> Response:
    return Response(
        content=json.dumps({
            "predictions": ["Environment variable response"],
            "source": "env_var",
            "priority": "environment_variable"
        }),
        media_type="application/json"
    )

# Decorator handlers (medium priority)
@sagemaker_standards.custom_ping_handler
async def decorator_ping(raw_request: Request) -> Response:
    return Response(
        content=json.dumps({
            "status": "healthy",
            "source": "decorator",
            "priority": "decorator"
        }),
        media_type="application/json"
    )

@sagemaker_standards.custom_invocation_handler
async def decorator_invoke(raw_request: Request) -> Response:
    return Response(
        content=json.dumps({
            "predictions": ["Decorator response"],
            "source": "decorator",
            "priority": "decorator"
        }),
        media_type="application/json"
    )

# Script functions (lowest priority)
async def custom_sagemaker_ping_handler():
    return {
        "status": "healthy",
        "source": "script",
        "priority": "script_function"
    }

async def custom_sagemaker_invocation_handler(request: Request):
    return {
        "predictions": ["Script function response"],
        "source": "script",
        "priority": "script_function"
    }
"""
            )
            script_path = f.name

        try:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)

            # Set environment variables to specify highest priority handlers
            env_vars = {
                SageMakerEnvVars.SAGEMAKER_MODEL_PATH: script_dir,
                SageMakerEnvVars.CUSTOM_SCRIPT_FILENAME: script_name,
                FastAPIEnvVars.CUSTOM_FASTAPI_PING_HANDLER: (
                    f"{script_name}:env_priority_ping"
                ),
                FastAPIEnvVars.CUSTOM_FASTAPI_INVOCATION_HANDLER: (
                    f"{script_name}:env_priority_invoke"
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
                # Test ping handler priority
                ping_response = requests.get(server.url_for("ping"))
                assert ping_response.status_code == 200
                ping_data = ping_response.json()

                # Environment variable has highest priority and should be used
                assert ping_data["priority"] == "environment_variable"
                assert ping_data["source"] == "env_var"

                # Test invocation handler priority
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

                # Environment variable has highest priority and should be used
                assert invoke_data["priority"] == "environment_variable"
                assert invoke_data["source"] == "env_var"

        finally:
            os.unlink(script_path)