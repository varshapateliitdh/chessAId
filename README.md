# ♟️ chessAId

chessAId is a conversational AI Chess teacher.

chessAId will also attend as you play a game against the computer (currently the [Stockfish](https://stockfishchess.org/) engine), answering questions and identifying opportunities to learn.

![Demo](https://github.com/varshapateliitdh/chessAId/blob/main/chessAId/assets/chessAId.gif)

Currently, you can play by dragging and dropping the pieces on the board and ask the chessAId chat for any help or review of the game. The moves you make on the board are automatically sent as context to the LLM and will consider the game history while helping you with the game.

## Usage
chessAId includes an application server and a separate [Langserve](https://github.com/langchain-ai/langserve) server for LLM orchestration. They can be built and launched with
```
docker-compose build base
docker-compose build langserver app

OPENAI_API_KEY=... docker-compose up
```
Alternatively, you can run locally with
```
OPENAI_API_KEY=... make start
```
