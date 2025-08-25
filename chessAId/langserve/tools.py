import asyncio
import os
import requests
from fastapi import WebSocket
from langchain.tools import StructuredTool, Tool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.globals import set_debug

from chessAId.app.app import make_move, websocket_endpoint
from chessAId.app.singleton_board_manager import board_manager

set_debug(True)


def _get_server_url():
    """Get URL for app server."""
    server_host = os.getenv("SERVER_HOST", "localhost")
    server_port = os.getenv("SERVER_PORT", "8000")
    return f"http://{server_host}:{server_port}"


SERVER_URL = _get_server_url()


class MakeMoveOnBoardInput(BaseModel):
    move: str = Field(
        ...,
        description="The UCI string of the move to make on the board, e.g., 'e2e4'",
    )


def _make_move_on_board(move: str) -> dict:
    """Use this tool to make a move on the board and broadcast it via WebSocket."""
    try:
        # Send the move to the backend endpoint
        response = requests.post(f"{SERVER_URL}/make_move_from_frontend/{move}")
        response_data = response.json()

        if "error" in response_data:
            return {"error": response_data["error"]}

        # Broadcast the move result to all connected WebSocket clients
        print(f"Broadcasting move result: {response_data}")  # Log before broadcasting
        asyncio.run(board_manager.broadcast(str(response_data)))

        return response_data
    except Exception as e:
        return {"error": str(e)}


class InitializeGameInput(BaseModel):
    player_side: str = Field(
        ...,
        description="The player's side of choice, either 'black' or 'white'",
    )


def _initialize_game(player_side: str) -> dict:
    """Use this tool to initialize a new chess game."""
    try:
        response = requests.post(f"{SERVER_URL}/start_new_game")
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


class ChessMoveInput(BaseModel):
    move: str = Field(
        ...,
        description="The UCI string of the move, e.g., 'd2d4'",
    )


def _make_chess_move(move_uci: str) -> dict:
    """Use this tool to make a chess move."""
    try:
        response = requests.post(f"{SERVER_URL}/make_move_from_frontend/{move_uci}")
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def _get_next_interesting_move() -> dict:
    """Use this tool to get the next interesting move according to the engine."""
    try:
        response = requests.post(f"{SERVER_URL}/get_engine_move")
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def get_tools() -> list[Tool]:
    make_move_on_board_tool = Tool.from_function(
        func=_make_move_on_board,
        name="make_move_on_board",
        description="Use this tool to make a move on the board and broadcast it to the frontend. Input the move in UCI format.",
        args_schema=MakeMoveOnBoardInput,
    )

    initialize_game_tool = Tool.from_function(
        func=_initialize_game,
        name="initialize_game",
        description="Use this tool to initialize a new chess game.",
        args_schema=InitializeGameInput,
    )

    chess_move_tool = Tool.from_function(
        func=_make_chess_move,
        name="make_chess_move",
        description="Use this tool to make a chess move. Input the move in UCI format.",
        args_schema=ChessMoveInput,
    )

    next_interesting_move_tool = StructuredTool.from_function(
        func=_get_next_interesting_move,
        name="get_next_interesting_move",
        description="Use this tool to identify the next interesting move.",
    )

    return [
        initialize_game_tool,
        chess_move_tool,
        next_interesting_move_tool,
        make_move_on_board_tool,
    ]
