import dill as pkl
import os

from add_group import load_groups

if __name__ == "__main__":
    path_to_pkl = os.getenv("REPORT_DATA_PATH", os.getcwd())
    groups = load_groups(path_to_pkl)
    print(groups.to_string())
