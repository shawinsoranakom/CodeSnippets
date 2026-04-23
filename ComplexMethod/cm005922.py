async def test_all_lfx_component_modules_directly_importable(self):
        """Test that all lfx component modules can be directly imported.

        This bypasses the lazy import system to catch actual import errors
        like deprecated imports, syntax errors, etc. Uses async for 3-5x
        performance improvement.
        """
        try:
            import lfx.components as components_pkg
        except ImportError:
            pytest.skip("lfx.components not available")

        # Collect all module names
        module_names = []
        for _, modname, _ in pkgutil.walk_packages(components_pkg.__path__, prefix=components_pkg.__name__ + "."):
            # Skip deactivated components
            if "deactivated" in modname:
                continue
            # Skip private modules
            if any(part.startswith("_") for part in modname.split(".")):
                continue
            module_names.append(modname)

        # Define async function to import a single module
        async def import_module_async(modname):
            """Import a module asynchronously."""
            try:
                # Run import in thread pool to avoid blocking
                await asyncio.to_thread(importlib.import_module, modname)
            except ImportError as e:
                error_msg = str(e)
                # Check if it's a missing optional dependency (expected)
                if any(
                    pkg in error_msg
                    for pkg in [
                        "agentics",
                        "agentics-py",
                        "crewai",
                        "langchain_openai",
                        "langchain_anthropic",
                        "langchain_google",
                        "langchain_cohere",
                        "langchain_pinecone",
                        "langchain_chroma",
                        "qdrant_client",
                        "pymongo",
                        "cassandra",
                        "weaviate",
                        "pinecone",
                        "chromadb",
                        "redis",
                        "elasticsearch",
                        "langchain_community",
                    ]
                ):
                    return ("skipped", modname, "missing optional dependency")
                return ("failed", modname, error_msg)
            except Exception as e:
                return ("failed", modname, f"{type(e).__name__}: {e}")
            else:
                return ("success", modname, None)

        # Import all modules in parallel
        results = await asyncio.gather(*[import_module_async(modname) for modname in module_names])

        # Process results
        failed_imports = []
        successful_imports = 0
        skipped_modules = []

        for status, modname, error in results:
            if status == "success":
                successful_imports += 1
            elif status == "skipped":
                skipped_modules.append(f"{modname} ({error})")
            else:  # failed
                failed_imports.append(f"{modname}: {error}")

        if failed_imports:
            failure_msg = (
                f"Failed to import {len(failed_imports)} component modules. "
                f"Successfully imported {successful_imports} modules. "
                f"Skipped {len(skipped_modules)} modules.\n\n"
                f"Failed imports:\n" + "\n".join(f"  • {f}" for f in failed_imports) + "\n\n"
                "This may indicate deprecated imports, syntax errors, or other issues."
            )
            pytest.fail(failure_msg)