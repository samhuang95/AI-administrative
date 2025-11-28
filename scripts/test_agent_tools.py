import importlib.util
import os
import json
import sys
import types

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_PATH = os.path.join(BASE, 'ai-agent', 'agent.py')

# Inject a dummy `google.adk.agents` module to avoid requiring the real SDK during tests
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

# Provide a minimal mock for `dotenv` used by the project so imports succeed in tests
dotenv_mod = types.ModuleType('dotenv')
def _load_dotenv(*a, **k):
    return None
def _dotenv_values(*a, **k):
    return {}
dotenv_mod.load_dotenv = _load_dotenv
dotenv_mod.dotenv_values = _dotenv_values
sys.modules['dotenv'] = dotenv_mod

# Mock `chromadb` and related utilities used by `ai-agent/rag_tool.py`
chromadb_mod = types.ModuleType('chromadb')
class DummyCollection:
    def __init__(self):
        self._docs = []
    def upsert(self, documents=None, ids=None, metadatas=None):
        # store documents for potential future use
        for i, d in enumerate(documents or []):
            self._docs.append({'id': ids[i] if ids else None, 'doc': d, 'meta': metadatas[i] if metadatas else None})
    def query(self, query_texts=None, n_results=3):
        # return empty results to indicate no match
        return {'documents': [[]], 'metadatas': [[]]}

class DummyPersistentClient:
    def __init__(self, path=None):
        self.path = path
    def get_or_create_collection(self, name, embedding_function=None):
        return DummyCollection()

chromadb_mod.PersistentClient = DummyPersistentClient

# chromadb.utils.embedding_functions.EmbeddingFunction base class
embedding_functions_mod = types.ModuleType('chromadb.utils.embedding_functions')
class EmbeddingFunction:
    pass
embedding_functions_mod.EmbeddingFunction = EmbeddingFunction
sys.modules['chromadb'] = chromadb_mod
sys.modules['chromadb.utils'] = types.ModuleType('chromadb.utils')
sys.modules['chromadb.utils.embedding_functions'] = embedding_functions_mod

# Mock `google.genai` used by rag_tool
genai_mod = types.ModuleType('google.genai')
class DummyModels:
    def embed_content(self, model=None, contents=None):
        class Resp:
            def __init__(self):
                class Emb:
                    def __init__(self):
                        self.values = [0.0] * 8
                self.embeddings = [Emb()]
        return Resp()

class DummyGenAIClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.models = DummyModels()

genai_mod.Client = DummyGenAIClient
sys.modules['google.genai'] = genai_mod
sys.modules['google'] = google_mod
sys.modules['google.genai.types'] = types.ModuleType('google.genai.types')

spec = importlib.util.spec_from_file_location('agent_mod', AGENT_PATH)
agent_mod = importlib.util.module_from_spec(spec)
# Ensure project root is on sys.path so imports like `data.query_data` resolve
if BASE not in sys.path:
    sys.path.insert(0, BASE)
# Also add the `data` directory to sys.path because some modules use bare `import query_data` imports
DATA_DIR = os.path.join(BASE, 'data')
if DATA_DIR not in sys.path:
    sys.path.insert(0, DATA_DIR)
spec.loader.exec_module(agent_mod)

outputs = {}

try:
    outputs['create'] = agent_mod.create_employee('Auto', 'Tester', 'auto.tester@example.com', 'QA', 'QA Engineer', 55000, '2025-11-28')
except Exception as e:
    outputs['create_exception'] = str(e)

try:
    outputs['get'] = agent_mod.get_employee('auto.tester@example.com')
except Exception as e:
    outputs['get_exception'] = str(e)

try:
    outputs['update'] = agent_mod.update_employee('auto.tester@example.com', {'position': 'Senior QA Engineer', 'salary': 60000})
except Exception as e:
    outputs['update_exception'] = str(e)

try:
    outputs['delete'] = agent_mod.delete_employee('auto.tester@example.com')
except Exception as e:
    outputs['delete_exception'] = str(e)

print(json.dumps(outputs, ensure_ascii=False, indent=2))
