var board;
var game;

// Fetch the initial board state from the backend
function initializeBoard() {
    fetch('/initialize_board')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Initialize chess.js with the returned FEN
                game = new Chess(data.fen);

                // Display piece IDs for debugging (optional)
                console.log("Piece IDs:", data.pieces);

                // Initialize the chessboard
                var board = Chessboard('board', {
                    draggable: true,
                    position: data.fen,
                    pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png',
                    dropOffBoard: 'snapback',
                    onDrop: function (source, target) {
                        // Make the move on the chess.js game logic
                        var piece = game.get(source); // Get the piece at the source square
                        if (piece && piece.type === 'p' && (target[1] === '8' || target[1] === '1')) {
                            // Show the promotion modal and save necessary data
                            showPromotionModal(piece.color, source, target);
                            return 'snapback'; // Temporarily snap the piece back
                        }
                    
                        // var move = game.move({ from: source, to: target });

                        
                        // // If the move is invalid, snap the piece back
                        // if (move === null) return 'snapback';

            
                        

                        // // Log the move for debugging
                        // console.log(`Move: ${move.from} -> ${move.to} (${move.san})`);
                        // console.log({move});
                        // console.log({source});
                        else{
                        sendMoveToBackend(source, target, game.fen());
                        
                        }// Show the move in the UI
                        //$('#moveLog').text(`Last move: ${move.from} -> ${move.to}`);

                        // Send the move to your API
                        //sendMoveToBackend(move.from, move.to, move.san);
                        
                        
                    }
                });
                window.pieceIds = data.pieces;
            }
        })
}
initializeBoard()

        


        
function handleGameEndingConditions() {
    if (game.in_checkmate()) {
        const winner = game.turn() === 'w' ? 'Black' : 'White';
        alert(`Checkmate! ${winner} wins!`);
    } else if (game.in_stalemate()) {
        alert("Stalemate! The game is a draw.");
    } else if (game.in_threefold_repetition()) {
        alert("Threefold repetition! The game is a draw.");
    } else if (game.insufficient_material()) {
        alert("Insufficient material! The game is a draw.");
    }
}

// Show the promotion modal
function showPromotionModal(color, source, target) {
    document.getElementById('promotion-modal').style.display = 'block';
    window.promotionData = { color, source, target };
}

function onPromotionPieceSelected(piece) {
    promote(piece, board); // Pass the board reference
}

// Handle promotion piece selection
function promote(piece, board) {
    const { color, source, target } = window.promotionData;
    document.getElementById('promotion-modal').style.display = 'none';

    // Get the current FEN from the board or game
    const currentFEN = game.fen();

    // Send the promotion move and FEN to the server
    fetch('/promote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            color,
            from: source,
            to: target,
            promotion: piece,
            fen: currentFEN  // Send the current board state
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the board with the new position (returned FEN string)
            game.load(data.newPosition);  // Update the game state
            board.position(game.fen());  // Update the board UI with new FEN
            handleGameEndingConditions();
            console.log(data.move);
        } else {
            console.error('Server failed to process promotion:', data.error);
        }
    })
    .catch(error => console.error('Error during promotion request:', error));
}

function sendMoveToBackend(from, to, fen) {
    fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from, to, fen })
    })
    .then(response => response.json())
    .then(data => {
        console.log("printing data");
        console.log(data);
        console.log("done with data object");
        if (data.success) {
            // Update the chessboard with the new FEN
            game.load(data.newPosition);  // Update the internal game logic
            board.position(game.fen());  // Update the visual board
            handleGameEndingConditions();
            // Update the scoreboard
        } else {
            console.error('Invalid move:', data.error);
            board.position(game.fen());
            alert('Invalid move: ' + data.error);
        }
    })
    .catch(error => console.error('Error sending move to backend:', error));
}


