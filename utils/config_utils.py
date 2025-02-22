import os

import yaml


def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)


def get_allowed_users():
    allowed_users_str = os.getenv("ALLOWED_USERS", "")
    return allowed_users_str.split(",") if allowed_users_str else []


if __name__ == "__main__":
    print(load_config())
    print(get_allowed_users())
