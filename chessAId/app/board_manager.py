import os
from typing import List, Dict

import chess
from fastapi import WebSocket, WebSocketDisconnect
from langserve import RemoteRunnable



LANGSERVE_HOST = os.getenv("LANGSERVE_HOST", "localhost")
LANGSERVE_SECRET = os.getenv("LANGSERVE_SECRET", "secret")
CHAT_HISTORY_LENGTH = 50  # Number of most recent (human, ai) exchanges to retain.



class BoardManager:
    def __init__(self):
        self.active_websockets: list[WebSocket] = []
        self.remote_runnable = RemoteRunnable(
            f"http://{LANGSERVE_HOST}:8001/chessAId", headers={"x-token": LANGSERVE_SECRET}
        )
        self.chat_history = []
        self._init_board_and_history(chess.STARTING_FEN)

    def _init_board_and_history(self, fen: str):
        self.board = chess.Board(fen)
        self.move_history: Dict[str, List[str]] = {
            "user_moves": [],
            "engine_moves": [],
            "fen_history": [self.board.fen()]
        }
        self.scores = {
            "user": 0,
            "engine": 0
        }

    def reset_board(self, fen: str):
        self._init_board_and_history(fen)

    def record_move(self, move_uci: str, by_user: bool = True):
        # Push move to board and update move history and FEN
        move = chess.Move.from_uci(move_uci)
        self.board.push(move)
        if by_user:
            self.move_history["user_moves"].append(move_uci)
        else:
            self.move_history["engine_moves"].append(move_uci)
        self.move_history["fen_history"].append(self.board.fen())

    def clear_chat_and_history(self):
        self.chat_history.clear()
        self._init_board_and_history(chess.STARTING_FEN)


    async def websocket_endpoint(self, websocket: WebSocket):
        print(f"BoardManager instance ID in websocket_endpoint: {id(self)}")  # Debug log
        await websocket.accept()
        self.active_websockets.append(websocket)
        print("WebSocket connection accepted")  # Log when a connection is accepted
        print(f"Current active WebSocket clients: {len(self.active_websockets)}")  # Log the number of active clients
        try:
            welcome_message = "Welcome to chessAId!"
            await websocket.send_text(welcome_message)
            while True:
                data = await websocket.receive_text()
                user_message = data
                await websocket.send_text(user_message)
                print("WE ARE HERE")
                try:
                    response_message = await self.remote_runnable.ainvoke(
                        {
                            "user_message": user_message,
                            "chat_history": self.chat_history,
                            "game_history": self.move_history or {}
                        }
                    )
                    print(response_message)
                    self.chat_history.append((user_message, response_message))
                    self.chat_history = self.chat_history[-CHAT_HISTORY_LENGTH:]
                    await websocket.send_text(response_message)
                except Exception as e:
                    await websocket.send_text("[ERROR] Sorry, something went wrong. Please try again.")
        except WebSocketDisconnect:
            self.active_websockets.remove(websocket)

    async def broadcast(self, message: str):
        print(f"BoardManager instance ID in broadcast: {id(self)}")  # Debug log
        print(f"Number of active WebSocket clients: {len(self.active_websockets)}")  # Log the number of active clients
        print(f"Broadcasting message: {message}")  # Log the broadcasted message
        disconnected_websockets = []
        for websocket in self.active_websockets:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected_websockets.append(websocket)

        # Remove disconnected websockets from the active list
        for websocket in disconnected_websockets:
            self.active_websockets.remove(websocket)
