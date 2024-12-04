import dill as pkl
import os

if __name__ == "__main__":
    data_path = os.getenv("REPORT_DATA_PATH", os.getcwd())
    users_filename = os.path.join(data_path, "users.pkl")
    with open(users_filename, "rb") as f:
        users = pkl.load(f)

    print(users.to_string())
