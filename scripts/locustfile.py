from locust import HttpUser, task, between
import random

EMAIL = "admin@vas.com"
PASSWORD = "admin1234"

class VASUser(HttpUser):
    wait_time = between(1, 3)
    token: str = ""

    def on_start(self):
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def get_health(self):
        self.client.get("/health")

    @task(2)
    def list_alerts(self):
        self.client.get(
            "/api/v1/alerts?skip=0&limit=20",
            headers=self.auth_headers(),
        )

    @task(1)
    def login(self):
        self.client.post(
            "/api/v1/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )