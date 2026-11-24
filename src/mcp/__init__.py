"""
src/mcp/__init__.py
Model Context Protocol (MCP) package for VoGenFlow.
"""

def __getattr__(name: str):
    from src.mcp import server
    if hasattr(server, name):
        return getattr(server, name)
    raise AttributeError(f"module 'src.mcp' has no attribute '{name}'")


__all__ = [
    "mcp",
    "VoGenFlowResolver",
    "vogenflow_get_project_ir",
    "vogenflow_get_specification",
    "vogenflow_get_ddl",
    "vogenflow_get_tasks",
    "vogenflow_query_architecture",
    "vogenflow_list_sessions",
    "main",
]
