import importlib.util
import importlib
import os
import sqlite3
import sys
import tempfile
import types

import pytest

# Prepare a temporary sqlite DB with required schema
SCHEMA = '''
CREATE TABLE employee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE,
    department TEXT,
    position TEXT,
    salary REAL,
    hire_date TEXT,
    supervisor_id INTEGER
);

CREATE TABLE performance_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    reviewer_employee_id INTEGER,
    score INTEGER,
    comments TEXT,
    created_at TEXT
);
'''


def _make_temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    return path


@pytest.fixture()
def tmp_db_path():
    path = _make_temp_db()
    yield path
    try:
        os.remove(path)
    except Exception:
        pass


def _mock_external_deps():
    """Install minimal mocks for google.adk.agents, dotenv, chromadb, google.genai
    so importing `ai-agent/agent.py` works in test environments without the SDKs.
    """
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


def _import_agent_with_db(db_path):
    # Ensure package imports resolve
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    # Insert data dir so local modules that use bare imports find them
    data_dir = os.path.join(repo_root, 'data')
    if data_dir not in sys.path:
        sys.path.insert(0, data_dir)

    # Import data modules and override their DEFAULT_DB_PATH to our temp DB
    import data.insert_data as insert_data
    import data.query_data as query_data
    import data.update_data as update_data
    import data.delete_data as delete_data

    insert_data.DEFAULT_DB_PATH = db_path
    query_data.DEFAULT_DB_PATH = db_path
    update_data.DEFAULT_DB_PATH = db_path
    delete_data.DEFAULT_DB_PATH = db_path

    # Now import agent
    spec = importlib.util.spec_from_file_location('agent_mod', os.path.join(repo_root, 'ai-agent', 'agent.py'))
    agent_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent_mod)
    return agent_mod


def test_agent_crud_flow(tmp_db_path):
    _mock_external_deps()
    agent = _import_agent_with_db(tmp_db_path)

    # Create
    r = agent.create_employee('Py', 'Test', 'py.test@example.com', 'Dev', 'Engineer', 70000, '2025-01-01')
    assert r['status'] == 'success'
    emp_id = r['id']

    # Get
    g = agent.get_employee('py.test@example.com')
    assert g['status'] == 'success'
    assert g['employee']['email'] == 'py.test@example.com'

    # Update
    u = agent.update_employee('py.test@example.com', {'position': 'Senior Engineer', 'salary': 80000})
    assert u['status'] == 'success'
    assert u['rows_updated'] == 1

    # Delete
    d = agent.delete_employee('py.test@example.com')
    assert d['status'] == 'success'
    assert d['rows_deleted'] == 1
