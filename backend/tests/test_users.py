def test_register_user(client):
    response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "password": "Strongpassword4"
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["username"] == "testuser"
    assert "id" in data
    assert "password" not in data  # ensure password not returned


def test_login_user(client):
    # Register first
    register_response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "password": "Strongpassword4"
        }
    )
    assert register_response.status_code == 201

    # Login (OAuth2 form → must use data=)
    response = client.post(
        "/users/login",
        data={
            "username": "testuser",
            "password": "Strongpassword4"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_read_current_user(client):
    # Register
    register_response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "password": "Strongpassword4"
        }
    )
    assert register_response.status_code == 201

    # Login
    login_response = client.post(
        "/users/login",
        data={
            "username": "testuser",
            "password": "Strongpassword4"
        }
    )
    assert login_response.status_code == 200

    login_data = login_response.json()
    assert "access_token" in login_data

    token = login_data["access_token"]

    # Call protected route
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    user_data = response.json()

    assert user_data["username"] == "testuser"