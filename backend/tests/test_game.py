def test_create_game(client):
    # Register
    client.post(
        "/users/register",
        json={"username": "player1", "password": "pPsdsdss123"}
    )

    # Login
    login = client.post(
        "/users/login",
        data={"username": "player1", "password": "pPsdsdss123"}
    )

    token = login.json()["access_token"]

    # Create game
    response = client.post(
        "/games/create_game",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["player1"] is not None
    assert data["player2"] is None
    assert data["status"] in ["waiting_for_player", "in_progress"]