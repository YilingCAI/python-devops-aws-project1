# ------------------------
# Liveness Probe Test
# ------------------------
def test_liveness(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data["details"]
    assert isinstance(data["details"]["uptime_seconds"], int)


# ------------------------
# Readiness Probe Test (DB connected)
# ------------------------
def test_readiness_success(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["details"]["database"] == "connected"


# ------------------------
# Readiness Probe Test (DB down)
# ------------------------
def test_readiness_failure(client_broken_db):
    response = client_broken_db.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["details"]["database"] == "not reachable"


# ------------------------
# Global Health Test (DB connected)
# ------------------------
def test_global_health(client):
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data["details"]
    assert "uptime_seconds" in data["details"]


# ------------------------
# Global Health Test (DB down)
# ------------------------
def test_global_health_failure(client_broken_db):
    response = client_broken_db.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["details"]["database"] == "not reachable"
    assert "uptime_seconds" in data["details"]