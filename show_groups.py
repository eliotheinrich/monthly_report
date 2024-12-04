import dill as pkl
import os

if __name__ == "__main__":
    data_path = os.getenv("REPORT_DATA_PATH", os.getcwd())
    groups_filename = os.path.join(data_path, "groups.pkl")
    with open(groups_filename, "rb") as f:
        groups = pkl.load(f)
        print(groups.to_string())
