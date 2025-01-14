import dill as pkl
import os

from add_users import load_users

if __name__ == "__main__":
    users = load_users()
    print(users.to_string())
