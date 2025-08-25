// ===== Star-field animation =====
let starsInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  const starField = document.getElementById("star-field");

  function addStars(starFieldWidth, starFieldHeight, noOfStars) {
    for (let i = 0; i < noOfStars; i++) {
      const star = document.createElement("div");
      star.className = "star";
      star.style.top = `${Math.floor(Math.random() * starFieldHeight)}px`;
      star.style.left = `${Math.floor(Math.random() * starFieldWidth)}px`;
      star.style.position = "absolute";
      starField.appendChild(star);
    }
  }

  function animateStars(starFieldWidth, speed) {
    const stars = Array.from(starField.children);

    function getStarColor(index) {
      if (index % 8 === 0) return "red";
      if (index % 10 === 0) return "yellow";
      if (index % 17 === 0) return "blue";
      return "white";
    }

    function getStarDistance(index) {
      if (index % 6 === 0) return "";
      if (index % 9 === 0) return "near";
      if (index % 2 === 0) return "far";
      return "";
    }

    function getStarRelativeSpeed(index) {
      if (index % 6 === 0) return 1;
      if (index % 9 === 0) return 2;
      if (index % 2 === 0) return -1;
      return 0;
    }

    if (starsInterval) clearInterval(starsInterval);

    starsInterval = setInterval(() => {
      stars.forEach((star, i) => {
        star.className = `star ${getStarColor(i)} ${getStarDistance(i)}`;
        const currentLeft = parseInt(star.style.left, 10);
        const newLeft =
          (currentLeft - (speed + getStarRelativeSpeed(i)) + starFieldWidth) %
          starFieldWidth;
        star.style.left = `${newLeft}px`;
      });
    }, 20);
  }

  function initStars() {
    starField.innerHTML = "";
    const width = window.innerWidth;
    const height = window.innerHeight;
    addStars(width, height, 50);
    animateStars(width, 2);
  }

  initStars();
  window.addEventListener("resize", initStars);
});

// ===== Chat WebSocket =====
const ws = new WebSocket("ws://localhost:8000/ws");
const messageElement = document.getElementById("message");
const imageElement = document.getElementById("image");
const chatMessagesElement = document.getElementById("chat-messages");
const chatContainerElement = document.getElementById("chat-container");

ws.onmessage = (event) => {
  console.log("WebSocket message received:", event.data); // Log the received message

  // Helper function to check if a string is valid JSON
  const isValidJSON = (message) => {
    try {
      JSON.parse(message);
      return true;
    } catch {
      return false;
    }
  };

  if (isValidJSON(event.data)) {
    const data = JSON.parse(event.data); // Parse the message as JSON
    console.log("Parsed WebSocket message:", data); // Log the parsed message

    if (data.fen) {
      console.log("Updating board position with FEN:", data.fen); // Log the FEN being used
      board.position(data.fen);
      lastFen = data.fen;
      localStorage.setItem("fen", data.fen);

      if (data.scores?.user !== undefined) {
        userScoreEl.innerText = data.scores.user;
      }
      if (data.scores?.engine !== undefined) {
        engineScoreEl.innerText = data.scores.engine;
      }

      if (data.game_status === "checkmate") {
        const winner = data.winner === "user" ? "You" : "Engine";
        messageElement.textContent = `Checkmate! ${winner} won the game.`;
        disableBoardInteraction();
      } else {
        messageElement.textContent = "Move updated via WebSocket!";
      }
    }
  } else {
    console.warn("Received plain text WebSocket message:", event.data);

    // Append plain text messages to the chat UI
    const li = document.createElement("li");
    li.innerText = event.data;
    li.className =
      chatMessagesElement.children.length % 2 === 0
        ? "message-white"
        : "message-teal";

    chatMessagesElement.insertBefore(li, chatMessagesElement.firstChild);
  }
};

chatContainerElement.addEventListener("scroll", updateMessageOpacity);

function updateMessageOpacity() {
  const containerHeight = chatContainerElement.offsetHeight;
  const messages = chatMessagesElement.querySelectorAll("li");

  messages.forEach((message) => {
    const messagePos = message.offsetTop - chatContainerElement.scrollTop;
    const fadeStart = 0.15 * containerHeight;
    const opacity =
      messagePos < fadeStart ? Math.max(0, messagePos / fadeStart) : 1;
    message.style.opacity = opacity;
    message.classList.add("transparent");
  });
}

// ===== Chat Input =====
const chatFormElement = document.getElementById("chat-form");
const chatInputElement = document.getElementById("chat-input");

chatFormElement.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = chatInputElement.value.trim();
  chatInputElement.value = "";
  if (message) ws.send(message);
});

// ===== Chessboard Init =====
let moveIndex = 0;
let lastFen = "start";

const userScoreEl = document.getElementById("user-score");
const engineScoreEl = document.getElementById("engine-score");

const board = Chessboard("chessboard1", {
  draggable: true,
  dropOffBoard: "trash",
  sparePieces: false,
  pieceTheme:
    "https://raw.githubusercontent.com/oakmac/chessboardjs/master/website/img/chesspieces/wikipedia/{piece}.png",
  position: "start",
  onDrop: async function (source, target) {
    if (!target || target.length !== 2) {
      messageElement.textContent = "Invalid drop.";
      board.position(lastFen);
      return;
    }

    const moveStr = source + target;
    try {
      const response = await fetch(`/make_move_from_frontend/${moveStr}`, {
        method: "POST",
      });
      const data = await response.json().catch(() => ({}));

      if (data.error) {
        console.log("Backend error for move", moveStr, data);
        messageElement.textContent = "Invalid Move!";
        board.position(lastFen);
        return;
      }

      if (!data.fen) {
        console.log("No FEN in backend response for move", moveStr, data);
        messageElement.textContent =
          "Unexpected server response. Move reverted.";
        board.position(lastFen);
        return;
      }

      // Only update the board if the move is valid
      board.position(data.fen);
      lastFen = data.fen;
      localStorage.setItem("fen", data.fen);
      moveIndex++;

      if (data.scores?.user !== undefined) {
        userScoreEl.innerText = data.scores.user;
      }

      if (data.game_status === "checkmate") {
        const winner = data.winner === "user" ? "You" : "Engine";
        messageElement.textContent = `Checkmate! ${winner} won the game.`;
        disableBoardInteraction();
        return;
      }

      messageElement.textContent = "User Move Made! Waiting for Engine...";

      const engineResponse = await fetch("/get_engine_move", {
        method: "POST",
      });
      const engineData = await engineResponse.json().catch(() => ({}));

      if (engineData.fen) {
        board.position(engineData.fen);
        lastFen = engineData.fen;
        localStorage.setItem("fen", engineData.fen);
        moveIndex++;

        if (engineData.scores?.engine !== undefined) {
          engineScoreEl.innerText = engineData.scores.engine;
        }

        if (engineData.game_status === "checkmate") {
          const winner = engineData.winner === "engine" ? "Engine" : "You";
          messageElement.textContent = `Checkmate! ${winner} won the game.`;
          disableBoardInteraction();
          return;
        }

        messageElement.textContent = "Engine Move Made!";
      } else {
        messageElement.textContent =
          engineData.error || "Engine error. Try again.";
      }
    } catch (error) {
      console.error("Error making move:", error);
      messageElement.textContent =
        "Error communicating with the server. Move reverted.";
      board.position(lastFen);
      return;
    }
  },
  onSnapbackEnd: function (piece, square, position, orientation) {
    // Add a highlight effect to the source square
    const squareEl = document.querySelector(`#chessboard1 .square-${square}`);
    if (squareEl) {
      squareEl.classList.add("snapback-highlight");
      setTimeout(() => {
        squareEl.classList.remove("snapback-highlight");
      }, 400);
    }
  },
});

// ===== Back button logic =====
document.getElementById("backBtn").addEventListener("click", async () => {
  try {
    const response = await fetch("/undo_last_move", { method: "POST" });
    const data = await response.json();
    if (data.error) {
      messageElement.textContent = data.error;
      return;
    }
    if (data.fen) {
      board.position(data.fen);
      localStorage.setItem("fen", data.fen);
      if (data.scores?.user !== undefined) {
        userScoreEl.innerText = data.scores.user;
      }
      if (data.scores?.engine !== undefined) {
        engineScoreEl.innerText = data.scores.engine;
      }
      messageElement.textContent = data.message || "Last move undone.";
    }
  } catch (error) {
    console.error("Error undoing last move:", error);
    messageElement.textContent = "Error undoing last move.";
  }
});

// ===== Clear button logic =====
document.getElementById("clearBtn").addEventListener("click", async () => {
  localStorage.removeItem("fen");
  board.position("start");

  try {
    const response = await fetch("/clear_backend_data", { method: "POST" });
    messageElement.textContent = response.ok
      ? "FEN cleared. Board reset. Backend data cleared."
      : "Failed to clear backend data.";
  } catch (error) {
    console.error("Error clearing backend data:", error);
    messageElement.textContent = "Error clearing backend data.";
  }
});

function disableBoardInteraction() {
  board.destroy(); // Destroy current board
  // Recreate the board in the final position, not start
  window.board = Chessboard("chessboard1", {
    position: lastFen,
    draggable: false,
    sparePieces: false,
    pieceTheme:
      "https://raw.githubusercontent.com/oakmac/chessboardjs/master/website/img/chesspieces/wikipedia/{piece}.png",
  });
}

// ===== WebSocket FEN Update Handling =====
ws.onmessage = (event) => {
  console.log("WebSocket message received:", event.data); // Log the received message

  // Helper function to check if a string is valid JSON
  const isValidJSON = (message) => {
    try {
      JSON.parse(message);
      return true;
    } catch {
      return false;
    }
  };

  if (isValidJSON(event.data)) {
    const data = JSON.parse(event.data); // Parse the message as JSON
    console.log("Parsed WebSocket message:", data); // Log the parsed message

    if (data.fen) {
      console.log("Updating board position with FEN:", data.fen); // Log the FEN being used
      board.position(data.fen);
      lastFen = data.fen;
      localStorage.setItem("fen", data.fen);

      if (data.scores?.user !== undefined) {
        userScoreEl.innerText = data.scores.user;
      }
      if (data.scores?.engine !== undefined) {
        engineScoreEl.innerText = data.scores.engine;
      }

      if (data.game_status === "checkmate") {
        const winner = data.winner === "user" ? "You" : "Engine";
        messageElement.textContent = `Checkmate! ${winner} won the game.`;
        disableBoardInteraction();
      } else {
        messageElement.textContent = "Move updated via WebSocket!";
      }
    }
  } else {
    console.warn("Received plain text WebSocket message:", event.data);

    // Append plain text messages to the chat UI
    const li = document.createElement("li");
    li.innerText = event.data;
    li.className =
      chatMessagesElement.children.length % 2 === 0
        ? "message-white"
        : "message-teal";

    chatMessagesElement.insertBefore(li, chatMessagesElement.firstChild);
  }
};
