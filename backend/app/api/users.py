@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Missing required fields!"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    insert_query = """
        INSERT INTO users (username, password, wins)
        VALUES (%s, %s, %s)
    """
    try:
        cur.execute(insert_query, (username, password, 0))
        conn.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({"message": "Username already exists!"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({"message": "An error occurred: " + str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/get-user-details", methods=["POST"])
def get_user_detail():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        select_query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cur.execute(select_query, (username, password))
        user = cur.fetchone()
        
        if user:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failed"}), 401
    except Exception as e:
        return jsonify({"message": "An error occurred: " + str(e)}), 500
    finally:
        cur.close()
        conn.close()


