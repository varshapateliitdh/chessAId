import os

import chess
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chessAId.app.utils import StockfishEngine
from chessAId.app.singleton_board_manager import board_manager


app = FastAPI()

# Mount static and templates directories relative to this file
base_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

stockfish_engine = StockfishEngine()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main index page."""
    return templates.TemplateResponse("index.html", {"request": request})



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Proxy websocket connection to board_manager."""
    return await board_manager.websocket_endpoint(websocket)


@app.post("/make_move_from_frontend/{move}")
async def make_move(move: str):
    """
    Make a move sent from frontend.
    Validate move, update board, and check for checkmate.
    """
    print(f"Received move: {move}")
    print(f"Legal moves: {[m.uci() for m in board_manager.board.legal_moves]}")
    try:
        uci_move = chess.Move.from_uci(move)
        if uci_move in board_manager.board.legal_moves:
            captured_piece = board_manager.board.piece_at(uci_move.to_square)
            if captured_piece:
                board_manager.scores["user"] += stockfish_engine.get_piece_value(captured_piece)
            board_manager.record_move(move, by_user=True)
            if board_manager.board.is_checkmate():
                return {
                    "fen": board_manager.board.fen(),
                    "move_history": board_manager.move_history,
                    "game_status": "checkmate",
                    "winner": "user",
                }
            return  {
                "fen": board_manager.board.fen(),
                "move_history": board_manager.move_history,
                "scores": board_manager.scores,
                "game_status": "ongoing",
            }
        else:
            return {"error": "Invalid move"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/get_engine_move")
async def engine_move():
    """Get the engine's next move, update board, and check for checkmate."""
    try:
        board = board_manager.board
        move = stockfish_engine.get_move(board)
        captured_piece = board.piece_at(move.to_square)
        if captured_piece:
            board_manager.scores["engine"] += stockfish_engine.get_piece_value(captured_piece)
        board_manager.record_move(move.uci(), by_user=False)
        if board.is_checkmate():
            return {
                "fen": board.fen(),
                "move_history": board_manager.move_history,
                "game_status": "checkmate",
                "winner": "engine",
            }
        return {
            "fen": board.fen(),
            "move_history": board_manager.move_history,
            "scores": board_manager.scores,
            "game_status": "ongoing",
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/start_new_game")
async def start_new_game():
    """Reset board and move history to start a new game."""
    board_manager.reset_board(chess.STARTING_FEN)
    return {"fen": board_manager.board.fen(), "message": "New game started"}


@app.post("/clear_backend_data")
async def clear_backend_data():
    """Clear backend game data including board, move history, and chat history."""
    board_manager.clear_chat_and_history()
    return {"message": "Backend game data cleared successfully."}

@app.post("/undo_last_move")
async def undo_last_move():
    """Undo the last move (user or engine) and update board and histories."""
    try:
        # Only undo if there is at least one move to undo
        if len(board_manager.board.move_stack) > 0:
            board_manager.board.pop()
            # Remove last move from move_history and fen_history
            if board_manager.move_history["fen_history"]:
                board_manager.move_history["fen_history"].pop()
            # Remove from user_moves or engine_moves depending on whose move it was
            if len(board_manager.move_history["engine_moves"]) > 0 and (len(board_manager.move_history["user_moves"]) == len(board_manager.move_history["engine_moves"])):
                board_manager.move_history["engine_moves"].pop()
            elif len(board_manager.move_history["user_moves"]) > 0:
                board_manager.move_history["user_moves"].pop()
            return {
                "fen": board_manager.board.fen(),
                "move_history": board_manager.move_history,
                "scores": board_manager.scores,
                "message": "Last move undone."
            }
        else:
            return {"error": "No moves to undo."}
    except Exception as e:
        return {"error": str(e)}