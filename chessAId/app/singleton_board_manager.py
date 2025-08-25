import os
from chessAId.app.board_manager import BoardManager

# Create a shared instance of BoardManager
board_manager = BoardManager()
print(f"Shared BoardManager instance created with ID: {id(board_manager)} in PID: {os.getpid()}")