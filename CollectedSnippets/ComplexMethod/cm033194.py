def test_connection(provider_type: str, config: dict):
        """
        Test connection to sandbox provider by executing a simple Python script.

        This creates a temporary sandbox instance and runs a test code to verify:
        - Connection credentials are valid
        - Sandbox can be created
        - Code execution works correctly

        Args:
            provider_type: Provider identifier
            config: Provider configuration dictionary

        Returns:
            dict with test results including stdout, stderr, exit_code, execution_time
        """
        try:
            from agent.sandbox.providers import (
                SelfManagedProvider,
                AliyunCodeInterpreterProvider,
                E2BProvider,
            )

            # Instantiate provider based on type
            provider_classes = {
                "self_managed": SelfManagedProvider,
                "aliyun_codeinterpreter": AliyunCodeInterpreterProvider,
                "e2b": E2BProvider,
            }

            if provider_type not in provider_classes:
                raise AdminException(f"Unknown provider type: {provider_type}")

            provider = provider_classes[provider_type]()

            # Initialize with config
            if not provider.initialize(config):
                raise AdminException(f"Failed to initialize provider '{provider_type}'")

            # Create a temporary sandbox instance for testing
            instance = provider.create_instance(template="python")

            if not instance or instance.status != "READY":
                raise AdminException(f"Failed to create sandbox instance. Status: {instance.status if instance else 'None'}")

            # Simple test code that exercises basic Python functionality
            test_code = """
# Test basic Python functionality
import sys
import json
import math

print("Python version:", sys.version)
print("Platform:", sys.platform)

# Test basic calculations
result = 2 + 2
print(f"2 + 2 = {result}")

# Test JSON operations
data = {"test": "data", "value": 123}
print(f"JSON dump: {json.dumps(data)}")

# Test math operations
print(f"Math.sqrt(16) = {math.sqrt(16)}")

# Test error handling
try:
    x = 1 / 1
    print("Division test: OK")
except Exception as e:
    print(f"Error: {e}")

# Return success indicator
print("TEST_PASSED")
"""

            # Execute test code with timeout
            execution_result = provider.execute_code(
                instance_id=instance.instance_id,
                code=test_code,
                language="python",
                timeout=10  # 10 seconds timeout
            )

            # Clean up the test instance (if provider supports it)
            try:
                if hasattr(provider, 'terminate_instance'):
                    provider.terminate_instance(instance.instance_id)
                    logging.info(f"Cleaned up test instance {instance.instance_id}")
                else:
                    logging.warning(f"Provider {provider_type} does not support terminate_instance, test instance may leak")
            except Exception as cleanup_error:
                logging.warning(f"Failed to cleanup test instance {instance.instance_id}: {cleanup_error}")

            # Build detailed result message
            success = execution_result.exit_code == 0 and "TEST_PASSED" in execution_result.stdout

            message_parts = [
                f"Test {success and 'PASSED' or 'FAILED'}",
                f"Exit code: {execution_result.exit_code}",
                f"Execution time: {execution_result.execution_time:.2f}s"
            ]

            if execution_result.stdout.strip():
                stdout_preview = execution_result.stdout.strip()[:200]
                message_parts.append(f"Output: {stdout_preview}...")

            if execution_result.stderr.strip():
                stderr_preview = execution_result.stderr.strip()[:200]
                message_parts.append(f"Errors: {stderr_preview}...")

            message = " | ".join(message_parts)

            return {
                "success": success,
                "message": message,
                "details": {
                    "exit_code": execution_result.exit_code,
                    "execution_time": execution_result.execution_time,
                    "stdout": execution_result.stdout,
                    "stderr": execution_result.stderr,
                }
            }

        except AdminException:
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            raise AdminException(f"Connection test failed: {str(e)}\\n\\nStack trace:\\n{error_details}")