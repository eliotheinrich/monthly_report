import dill as pkl
import os

from load_data import load_users 

if __name__ == "__main__":
    path_to_pkl = os.getenv("REPORT_DATA_PATH", os.getcwd())
    users = load_users(path_to_pkl)
    print(users.to_string())
