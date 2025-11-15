"""Small importer that loads the package __init__.py by path (mimics ADK loader)
and prints whether importing the package succeeds and what `agent.root_agent` is.
"""
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

pkg_init = Path(__file__).resolve().parent / "__init__.py"
spec = spec_from_file_location("ai-agent", str(pkg_init))
mod = module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print("Loaded package module name:", mod.__name__)
    agent_mod = getattr(mod, "agent", None)
    print("agent attribute present:", agent_mod is not None)
    if agent_mod is not None:
        root_agent = getattr(agent_mod, "root_agent", None)
        print("root_agent:", type(root_agent), root_agent)
except Exception as e:
    print("Import failed:", repr(e))
