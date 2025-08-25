#!/usr/bin/env python
import os

from fastapi import Depends, FastAPI, Header, HTTPException
from typing import Dict, List, Tuple, Any
from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langserve import add_routes
from typing_extensions import Annotated

from chessAId.langserve.agent import get_agent, get_tools


HOST = os.getenv("LANGSERVE_HOST", "localhost")
LANGSERVE_SECRET = os.getenv("LANGSERVE_SECRET", "secret")


async def verify_token(x_token: Annotated[str, Header()]) -> None:
    """Verify the token is valid."""
    # Replace this with your actual authentication logic
    if x_token != LANGSERVE_SECRET:
        raise HTTPException(status_code=400, detail="X-Token header invalid")


app = FastAPI(
    title="chessAId chat server.",
    version="1.0",
    dependencies=[Depends(verify_token)],
)


class AgentInput(BaseModel):
    user_message: str
    chat_history: List[Tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )
    game_history: Dict[str, Any]

tools = get_tools()
agent = get_agent()
agent_executor = AgentExecutor(agent=agent, tools=tools).with_types(
    input_type=AgentInput
) | (lambda x: x["output"])

add_routes(
    app,
    agent_executor,
    path="/chessAId",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=8001)
