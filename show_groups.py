import dill as pkl
import os

from add_group import load_groups

if __name__ == "__main__":
    groups = load_groups()
    print(groups.to_string())
