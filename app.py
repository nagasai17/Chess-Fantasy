from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

from flask_cors import CORS

  # This will allow all CORS requests
import chess
import MappingforIds

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

import sqlite3
#initialising database
def init_db():
    conn = sqlite3.connect('chess_fantasy.db')
    cursor = conn.cursor()

    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT,
            total_points INTEGER DEFAULT 0
        )
    ''')

    # Create Selected Pieces table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS selected_pieces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            piece TEXT NOT NULL,
            color TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()

# Call this function to initialize the database
init_db()



#Creating the Board

@app.route('/initialize_board', methods=['GET'])
def initialize_board():
    board = chess.Board()  # Start with the initial position
    piece_ids = {}

    # Traverse all squares on the board
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_id = MappingforIds.MappingIds[chess.square_name(square)]
            piece_ids[chess.square_name(square)] = {
                "id": piece_id,
                "type": piece.piece_type,
                "color": "white" if piece.color else "black",
                "place" : chess.square_name(square)
            }
            MappingforIds.GettingIdsFromBoard[square] = piece_id

    return jsonify({
        "success": True,
        "fen": board.fen(),  # Initial FEN for the board position
        "pieces": piece_ids
    })

#adding User
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    username = data['username']
    email = data.get('email', None)

    conn = sqlite3.connect('chess_fantasy.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO users (username, email) VALUES (?, ?)', (username, email))
    conn.commit()
    conn.close()

    return jsonify(success=True, message="User added successfully!")


@app.route('/select_piece', methods=['POST'])
def select_piece():
    data = request.json
    user_id = data['user_id']
    piece = data['piece']
    color = data['color']

    conn = sqlite3.connect('chess_fantasy.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO selected_pieces (user_id, piece, color) VALUES (?, ?, ?)', (user_id, piece, color))
    conn.commit()
    conn.close()

    return jsonify(success=True, message="Piece selected successfully!")


def update_points(user_id, points):
    conn = sqlite3.connect('chess_fantasy.db')
    cursor = conn.cursor()

    # Update total points for the user
    cursor.execute('UPDATE users SET total_points = total_points + ? WHERE user_id = ?', (points, user_id))

    # Commit the changes
    conn.commit()
    conn.close()

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
    if (piece and current_turn and piece.color != chess.WHITE) or (not current_turn and piece.color != chess.BLACK):
        return jsonify(success=False, error="It's not your turn")
    
    if move in board.legal_moves:
            try:
                iscaptured  = False if board.piece_at(to_square_index) is None else True 
                if iscaptured:
                    captured_piece = board.piece_at(to_square_index)
                board.push(move)
                MappingforIds.GettingIdsFromBoard[to_square_index] = MappingforIds.GettingIdsFromBoard[from_square_index]
                MappingforIds.GettingIdsFromBoard.pop(from_square_index)
                # Check if the move involved capturing a piece
                print(move,iscaptured,MappingforIds.GettingIdsFromBoard)
                if iscaptured:
                    capturing_piece = board.piece_at(to_square_index)
                    if capturing_piece:
                        # Points system for captured pieces
                        points = {
                            chess.PAWN: 1,
                            chess.KNIGHT: 3,
                            chess.BISHOP: 3,
                            chess.ROOK: 5,
                            chess.QUEEN: 9
                        }
                        
                        if(points[capturing_piece.piece_type]- points[captured_piece.piece_type] <=0):
                            pointstobeadded = points[captured_piece.piece_type]
                        else:
                            pointstobeadded = points[capturing_piece.piece_type]- points[captured_piece.piece_type]
                        print(f"Points added: {pointstobeadded} because {capturing_piece.piece_type} captured {captured_piece.piece_type} with Id of the killing piece is {MappingforIds.GettingIdsFromBoard[to_square_index]}   and Killing piece is at {chess.square_name(to_square_index)}")
                        MappingforIds.totalpoints[MappingforIds.MappingSquares[MappingforIds.GettingIdsFromBoard[to_square_index]]] += pointstobeadded
                        print(MappingforIds.totalpoints)
                        # You can add points to a player’s score here.

                        #trying to update the points!!!!
                        # Find the user who owns the captured piece and update their score
                    # conn = sqlite3.connect('chess_fantasy.db')
                    # cursor = conn.cursor()

                    # cursor.execute('''
                    #     SELECT user_id FROM selected_pieces WHERE piece = ? AND color = ?
                    # ''', (str(captured_piece), 'black' if board.turn else 'white'))

                    # result = cursor.fetchone()
                    # if result:
                    #     update_points(result[0], points)

                return jsonify(success=True, newPosition=board.fen(), move = move)

            except Exception as e:
                return jsonify(success=False, error=f"Error pushing move: {str(e)}")

    else:
        return jsonify(success=False, error="Invalid move for the current player")

if __name__ == '__main__':
    socketio.run(app, debug=True)
