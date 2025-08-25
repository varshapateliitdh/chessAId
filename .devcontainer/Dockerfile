FROM python:3.9

WORKDIR /chessAId

COPY . /chessAId

RUN pip install poetry
RUN poetry install

RUN chmod +x stockfish/download.sh
RUN ./stockfish/download.sh
