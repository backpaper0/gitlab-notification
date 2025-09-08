import logging
import sqlite3
import time
from typing import Any, Dict, List

import requests
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    gitlab_personal_access_token: str = ""
    gitlab_todos_api_endpoint: str = ""
    owattayo_api_endpoint: str = ""
    db_path: str = "gitlab-notification.db"
    interval_seconds: int = 60


settings = Settings()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitLabNotificationService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.settings.db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS processed_todos (max_id INTEGER PRIMARY KEY)"
            )
            cursor = conn.execute("SELECT max_id FROM processed_todos")
            result = cursor.fetchone()
            if not result:
                conn.execute("INSERT INTO processed_todos (max_id) VALUES (0)")
                conn.commit()

    def get_last_processed_id(self) -> int:
        with sqlite3.connect(self.settings.db_path) as conn:
            cursor = conn.execute("SELECT max_id FROM processed_todos")
            result = cursor.fetchone()
            return result[0] if result else 0

    def update_last_processed_id(self, max_id: int):
        with sqlite3.connect(self.settings.db_path) as conn:
            conn.execute("UPDATE processed_todos SET max_id = ?", (max_id,))
            conn.commit()

    def fetch_gitlab_todos(self) -> List[Dict[str, Any]]:
        headers = {"PRIVATE-TOKEN": self.settings.gitlab_personal_access_token}

        try:
            response = requests.get(
                self.settings.gitlab_todos_api_endpoint,
                headers=headers,
                params={"state": "pending"},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch GitLab todos: {e}")
            return []

    def notify_owattayo(self, prompt: str, url: str) -> bool:
        try:
            response = requests.post(
                self.settings.owattayo_api_endpoint, json={"prompt": prompt, "url": url}
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to notify Owattayo: {e}")
            return False

    def process_todos(self):
        todos = self.fetch_gitlab_todos()
        if not todos:
            return

        last_processed_id = self.get_last_processed_id()
        new_todos = [todo for todo in todos if todo["id"] > last_processed_id]

        if not new_todos:
            logger.info("No new todos to process")
            return

        logger.info(f"Processing {len(new_todos)} new todos")

        max_id = last_processed_id
        for todo in new_todos:
            if todo["state"] != "pending":
                continue

            author_username = todo.get("author", {}).get("username", "Unknown")
            body = todo.get("body", "")
            target_url = todo.get("target_url", "")

            prompt = f"{author_username}: {body}"

            if self.notify_owattayo(prompt, target_url):
                logger.info(f"Notified Owattayo for todo {todo['id']}")
                max_id = max(max_id, todo["id"])
            else:
                logger.error(f"Failed to notify Owattayo for todo {todo['id']}")

        if max_id > last_processed_id:
            self.update_last_processed_id(max_id)

    def run(self):
        logger.info("Starting GitLab notification service")
        logger.info(f"Polling interval: {self.settings.interval_seconds} seconds")

        while True:
            try:
                self.process_todos()
                time.sleep(self.settings.interval_seconds)
            except KeyboardInterrupt:
                logger.info("Service stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(self.settings.interval_seconds)


def main():
    service = GitLabNotificationService(settings)
    service.run()


if __name__ == "__main__":
    main()
