@app.route('/create_game', methods=['POST'])
def create_game():
    data = request.get_json()
    username = data.get('username')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return jsonify({'message': 'Invalid username'}), 400
    
    game_id = str(uuid.uuid4())
    board = ''.join([" "] * 9)
    cur.execute(
        "INSERT INTO games (game_id, player1, player2, board, current_turn, winner) VALUES (%s, %s, %s, %s, %s, %s)",
        (game_id, username, None, board, username, None))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'game_id': game_id})

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.get_json()
    username = data.get('username')
    game_id = data.get('game_id')
    move = data.get('move')

    if not username or not game_id or move is None:
        return jsonify({'message': 'Username, game ID, and move are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)

        cur.execute("SELECT * FROM games WHERE game_id = %s FOR UPDATE", (game_id,))
        game = cur.fetchone()
        if not game:
            return jsonify({'message': 'Invalid game ID'}), 400

        board = list(game[3])
        current_turn = game[4]
        winner = game[5]

        if winner:
            return jsonify({'message': 'Game already has a winner', 'board': ''.join(board), 'winner': winner})

        if username != current_turn:
            return jsonify({'message': 'It\'s not your turn'}), 400

        if board[move] != " ":
            return jsonify({'message': 'Invalid move'}), 400

        board[move] = 'X' if current_turn == game[1] else 'O'
        winner = check_winner(board)
        next_turn = game[2] if current_turn == game[1] else game[1]

        if winner and winner != "Draw":
            update_wins_query = "UPDATE users SET wins = wins + 1 WHERE username = %s"
            winner_username = game[1] if winner == 'X' else game[2]
            cur.execute(update_wins_query, (winner_username,))

        update_query = "UPDATE games SET board = %s, current_turn = %s, winner = %s WHERE game_id = %s"
        cur.execute(update_query, (''.join(board), None if winner else next_turn, winner, game_id))
        conn.commit()

        return jsonify({
            'message': 'Move made',
            'board': ''.join(board),
            'current_player': next_turn if not winner else None,
            'winner': winner
        })
    except Exception as e:
        return jsonify({'message': 'An error occurred: ' + str(e)}), 500
    finally:
        cur.close()
        conn.close

@app.route('/game_state/<game_id>', methods=['GET'])
def get_game_state(game_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cur.fetchone()
        if not game:
            return jsonify({'message': 'Invalid game ID'}), 400

        game_state = {
            'game_id': game_id,
            'player1': game[1],
            'player2': game[2],
            'board': game[3],
            'current_turn': game[4],
            'winner': game[5]
        }
        return jsonify(game_state)
    except Exception as e:
        return jsonify({'message': 'An error occurred: ' + str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.get_json()
    username = data.get('username')
    game_id = data.get('game_id')
    move = data.get('move')

    if not username or not game_id or move is None:
        return jsonify({'message': 'Username, game ID, and move are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)

        cur.execute("SELECT * FROM games WHERE game_id = %s FOR UPDATE", (game_id,))
        game = cur.fetchone()
        if not game:
            return jsonify({'message': 'Invalid game ID'}), 400

        board = list(game[3])
        current_turn = game[4]
        winner = game[5]

        if winner:
            return jsonify({'message': 'Game already has a winner', 'board': ''.join(board), 'winner': winner})

        if username != current_turn:
            return jsonify({'message': 'It\'s not your turn'}), 400

        if board[move] != " ":
            return jsonify({'message': 'Invalid move'}), 400

        board[move] = 'X' if current_turn == game[1] else 'O'
        winner = check_winner(board)
        next_turn = game[2] if current_turn == game[1] else game[1]

        if winner and winner != "Draw":
            update_wins_query = "UPDATE users SET wins = wins + 1 WHERE username = %s"
            winner_username = game[1] if winner == 'X' else game[2]
            cur.execute(update_wins_query, (winner_username,))

        update_query = "UPDATE games SET board = %s, current_turn = %s, winner = %s WHERE game_id = %s"
        cur.execute(update_query, (''.join(board), None if winner else next_turn, winner, game_id))
        conn.commit()

        return jsonify({
            'message': 'Move made',
            'board': ''.join(board),
            'current_player': next_turn if not winner else None,
            'winner': winner
        })
    except Exception as e:
        return jsonify({'message': 'An error occurred: ' + str(e)}), 500
    finally:
        cur.close()
        conn.close