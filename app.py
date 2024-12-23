from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

from flask_cors import CORS

  # This will allow all CORS requests
import chess

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

# Serve the main page
@app.route('/')
def index():
    return render_template('index.html')

# Handle move updates
@app.route('/predict-points', methods=['POST'])
def predict_points():
    data = request.json
    fen = data.get('fen')  # FEN string of the current board state
    # Logic to calculate points for the move
    points = {"points": 10}  # Mock points
    return jsonify(points)

@app.route('/promote', methods=['POST'])
def promote():
    data = request.json
    try:
        source = data['from']
        target = data['to']
        promotion = data.get('promotion', '').lower()  # 'q', 'r', 'b', or 'n'
        fen = data['fen']

        # Load the board
        board = chess.Board(fen)

        # Ensure the promotion piece is valid
        if promotion not in ['q', 'r', 'b', 'n']:
            return jsonify(success=False, error="Invalid promotion piece.")

        source_square = chess.parse_square(source)
        target_square = chess.parse_square(target)

        # Validate the source piece is a pawn
        source_piece = board.piece_at(source_square)
        if not source_piece or source_piece.piece_type != chess.PAWN:
            return jsonify(success=False, error="Source square does not contain a pawn.")

        # Determine the rank and direction
        if board.turn:  # White's turn
            promotion_rank = 7  # White promotes on rank 7
            direction = 1  # White pawns move up
        else:  # Black's turn
            promotion_rank = 0  # Black promotes on rank 0
            direction = -1  # Black pawns move down

        # Validate the target square is on the promotion rank
        if chess.square_rank(target_square) != promotion_rank:
            return jsonify(success=False, error="Target square is not on the promotion rank.")

        # Check if the move is valid
        source_file = chess.square_file(source_square)
        target_file = chess.square_file(target_square)

        # Handle normal pawn promotion (no capture)
        if source_file == target_file:
            if board.piece_at(target_square) is not None:
                return jsonify(success=False, error="Target square is occupied for a non-capture move.")
            if chess.square_rank(source_square) + direction != promotion_rank:
                return jsonify(success=False, error="Invalid rank transition for promotion.")

        # Handle capture promotion
        elif abs(source_file - target_file) == 1:  # Capturing moves must be diagonal
            if board.piece_at(target_square) is None:
                return jsonify(success=False, error="No piece to capture on the target square.")
            if chess.square_rank(source_square) + direction != promotion_rank:
                return jsonify(success=False, error="Invalid rank transition for capture promotion.")
        else:
            return jsonify(success=False, error="Invalid pawn movement for promotion.")

        # Construct the move and push it
        move = chess.Move(source_square, target_square, promotion=chess.PIECE_SYMBOLS.index(promotion))
        board.push(move)

        return jsonify(success=True, newPosition=board.fen())
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/move', methods=['POST'])
def make_move():
    data = request.json
    from_square = data['from']
    to_square = data['to']
    fen = data['fen']

    # Initialize the board using the provided FEN string
    board = chess.Board(fen)

    # Parse the square notation from UCI format to internal square index
    from_square_index = chess.parse_square(from_square)
    to_square_index = chess.parse_square(to_square)

    # Check whose turn it is
    current_turn = board.turn  # True means white's turn, False means black's turn

    # Create the move object using the parsed indices
    move = chess.Move(from_square_index, to_square_index)
    
    # Debugging output to check the move validity
    print(f"Move attempted: {move.uci()}")
    
    print(current_turn)
    piece = board.piece_at(from_square_index)
    print(piece)
    # Validate the move: Check if it's the correct player's turn
    if (current_turn and piece.color != chess.WHITE) or (not current_turn and piece.color != chess.BLACK):
        return jsonify(success=False, error="It's not your turn")
    
    if move in board.legal_moves:
            try:
                iscaptured  = False if board.piece_at(to_square_index) is None else True 
                board.push(move)
                
                # Check if the move involved capturing a piece
                print(move,iscaptured)
                if iscaptured:
                    captured_piece = board.piece_at(to_square_index)
                    if captured_piece:
                        # Points system for captured pieces
                        points = {
                            chess.PAWN: 1,
                            chess.KNIGHT: 3,
                            chess.BISHOP: 3,
                            chess.ROOK: 5,
                            chess.QUEEN: 9
                        }.get(captured_piece.piece_type, 0)

                        print(f"Points added: {points}")
                        # You can add points to a player’s score here.

                return jsonify(success=True, newPosition=board.fen(), move = move)

            except Exception as e:
                return jsonify(success=False, error=f"Error pushing move: {str(e)}")

    else:
        return jsonify(success=False, error="Invalid move for the current player")

    


if __name__ == '__main__':
    socketio.run(app, debug=True)
