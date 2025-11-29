
import os
import sys
import asyncio
from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from google.adk import Runner
from google.adk.sessions import InMemorySessionService


# Ensure we can import from ai-agent
sys.path.append(os.path.join(os.getcwd(), "ai-agent"))

# Load environment variables
env_path = os.path.join("ai-agent", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

try:
    import agent as agent_module
    root_agent = agent_module.root_agent
    print("Successfully imported root_agent")
except ImportError as e:
    print(f"Error importing root_agent: {e}")
    sys.exit(1)

# MockMessage definition for ADK
class MockMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content
        self.parts = [{"text": content}]
    def model_dump(self):
        return {"role": self.role, "content": self.content, "parts": self.parts}
    def model_copy(self, **kwargs):
        return self

# Initialize ADK components
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, session_service=session_service, app_name="agents")

# Track running agent tasks per session so they can be cancelled
running_tasks: dict[str, asyncio.Task] = {}
tasks_lock = asyncio.Lock()
# --- FastAPI App ---

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (our frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    text: str
    user_id: str = "web_user"
    session_id: str = "web_session"

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    print(f"Received chat request: {request.text}")

    # Ensure session exists
    try:
        # Try to get session, if fails or not exists, create it.
        # InMemorySessionService doesn't have a simple "exists" check exposed easily,
        # but create_session might fail if it exists or just overwrite?
        # Actually, for InMemory, we can just try to create and ignore error if it says "already exists"
        # or just rely on the runner to handle it?
        # The runner throws "Session not found" if not created.
        # Let's try to create it every time for a new session_id, or handle the error.
        # Since we don't know if it exists, we can try to create it.
        # But InMemorySessionService stores sessions in memory.
        pass
    except Exception:
        pass

    # We need to ensure the session exists.
    # A simple way is to try to create it and catch the exception if it already exists.
    try:
        await session_service.create_session(session_id=request.session_id, user_id=request.user_id, app_name="agents")
    except Exception as e:
        # If it fails, it might be because it already exists.
        # ADK's InMemorySessionService might raise an error or just work.
        # Let's assume if it fails, it might be fine or we catch specific error.
        # print(f"Session creation note: {e}")
        pass

    response_text = ""
    user_input = MockMessage(role="user", content=request.text)

    async def run_agent() -> None:
        nonlocal response_text
        try:
            async for event in runner.run_async(user_id=request.user_id, session_id=request.session_id, new_message=user_input):
                if hasattr(event, "content") and hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        # Support both object and dict-like parts
                        text = None
                        if isinstance(part, dict):
                            text = part.get("text")
                        else:
                            # some SDK objects expose .text attribute
                            if hasattr(part, "text"):
                                text = part.text
                        if text:
                            response_text += text
        except asyncio.CancelledError:
            # Task was cancelled by /cancel; just exit to allow returning partial text
            print(f"Agent turn for session {request.session_id} cancelled by user")
            raise
        except Exception as e:
            print(f"Error in agent turn: {e}")
            raise

    # Create and store task so it can be cancelled by another request
    # If there's an existing running task for this session, cancel it first to avoid orphaned tasks
    async with tasks_lock:
        existing = running_tasks.get(request.session_id)
        if existing and not existing.done():
            print(f"Found existing running task for session {request.session_id}, cancelling it before starting a new one")
            existing.cancel()
            try:
                # wait a short time for it to finish cleanup
                await asyncio.wait_for(existing, timeout=2.0)
            except asyncio.TimeoutError:
                print(f"Existing task for session {request.session_id} did not finish within timeout")
            except Exception:
                pass

        task = asyncio.create_task(run_agent())
        running_tasks[request.session_id] = task

    try:
        await task
    except asyncio.CancelledError:
        # Return partial response when cancelled
        pass
    except Exception as e:
        # Propagate other errors as HTTP 500
        async with tasks_lock:
            running_tasks.pop(request.session_id, None)
        print(f"Agent execution error for session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        async with tasks_lock:
            # Clean up stored task reference only if it's this task (avoid removing newer task)
            cur = running_tasks.get(request.session_id)
            if cur is task:
                running_tasks.pop(request.session_id, None)

    return ChatResponse(response=response_text)


class CancelRequest(BaseModel):
    session_id: str = "web_session"


@app.post("/cancel")
async def cancel_endpoint(req: CancelRequest):
    """Cancel a running agent turn for the given session_id.

    Client can call this while `/chat` is waiting to stop the current generation.
    """
    async with tasks_lock:
        task = running_tasks.get(req.session_id)
        if not task:
            raise HTTPException(status_code=404, detail="No running task for this session")
        # Cancel the task
        task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        return {"status": "cancelled", "session_id": req.session_id}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

    return {"status": "cancel_requested", "session_id": req.session_id}

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
