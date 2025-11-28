import importlib.util
import os
import sys
import types
import json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_PATH = os.path.join(BASE, 'ai-agent', 'agent.py')

# Insert repo root and data dir so local imports resolve
if BASE not in sys.path:
    sys.path.insert(0, BASE)
DATA_DIR = os.path.join(BASE, 'data')
if DATA_DIR not in sys.path:
    sys.path.insert(0, DATA_DIR)

# Minimal mocks for external dependencies used by agent.py / rag_tool
google_mod = types.ModuleType('google')
adk_mod = types.ModuleType('google.adk')
agents_mod = types.ModuleType('google.adk.agents')
class DummyLlmAgent:
    def __init__(self, *args, **kwargs):
        self.tools = kwargs.get('tools', [])
agents_mod.LlmAgent = DummyLlmAgent
sys.modules['google'] = google_mod
sys.modules['google.adk'] = adk_mod
sys.modules['google.adk.agents'] = agents_mod

dotenv_mod = types.ModuleType('dotenv')
dotenv_mod.load_dotenv = lambda *a, **k: None
dotenv_mod.dotenv_values = lambda *a, **k: {}
sys.modules['dotenv'] = dotenv_mod

# chromadb mocks
chromadb_mod = types.ModuleType('chromadb')
class DummyCollection:
    def upsert(self, *a, **k):
        return None
    def query(self, *a, **k):
        return {'documents': [[]], 'metadatas': [[]]}
class DummyPersistentClient:
    def __init__(self, path=None):
        pass
    def get_or_create_collection(self, name, embedding_function=None):
        return DummyCollection()
chromadb_mod.PersistentClient = DummyPersistentClient
sys.modules['chromadb'] = chromadb_mod
sys.modules['chromadb.utils'] = types.ModuleType('chromadb.utils')
sys.modules['chromadb.utils.embedding_functions'] = types.ModuleType('chromadb.utils.embedding_functions')
setattr(sys.modules['chromadb.utils.embedding_functions'], 'EmbeddingFunction', object)

# google.genai mock
genai_mod = types.ModuleType('google.genai')
class DummyModels:
    def embed_content(self, *a, **k):
        class R:
            def __init__(self):
                class E:
                    def __init__(self):
                        self.values = [0.0] * 8
                self.embeddings = [E()]
        return R()
class DummyClient:
    def __init__(self, api_key=None):
        self.models = DummyModels()
genai_mod.Client = DummyClient
sys.modules['google.genai'] = genai_mod
sys.modules['google.genai.types'] = types.ModuleType('google.genai.types')

# Now import agent module
spec = importlib.util.spec_from_file_location('agent_mod', AGENT_PATH)
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)

# Run a small create -> update -> get flow
out = {}
try:
    c = agent_mod.create_employee('Sim', 'User', 'sim.user@example.com', 'Eng', 'Developer', 70000, '2025-01-01')
    out['create'] = c
    if c.get('status') == 'success':
        # call update_employee with explicit args (new simpler signature)
        u = agent_mod.update_employee('sim.user@example.com', position='Lead Developer', salary=85000)
        out['update'] = u
        g = agent_mod.get_employee('sim.user@example.com')
        out['get_after_update'] = g
        # cleanup
        d = agent_mod.delete_employee('sim.user@example.com')
        out['delete'] = d
except Exception as e:
    out['exception'] = str(e)

print(json.dumps(out, ensure_ascii=False, indent=2))
