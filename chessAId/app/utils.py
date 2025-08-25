import os
import chess
import chess.engine
from typing import Optional


class StockfishEngine:
    def __init__(self, skill_level: int = 3, engine_path: Optional[str] = None):
        self.engine_path = engine_path or os.getenv(
            "STOCKFISH_ENGINE_PATH",
            "/workspaces/chesster-main/stockfish/stockfish-ubuntu-x86-64-modern",
        )
        self.skill_level = skill_level
        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        self.engine.configure({"Skill Level": self.skill_level})
        self.PIECE_VALUES = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # Don't count king for points
        }

    def get_move(self, board: chess.Board, time_limit: float = 0.1) -> chess.Move:
        result = self.engine.play(board, chess.engine.Limit(time=time_limit))
        return result.move

    def close(self) -> None:
        self.engine.quit()


    def get_piece_value(self, piece: Optional[chess.Piece]) -> int:
        if piece is None:
            return 0
        return self.PIECE_VALUES.get(piece.piece_type, 0)


# Example usage:
# engine = StockfishEngine(skill_level=5)
# move = engine.get_move(board)
# engine.close()

