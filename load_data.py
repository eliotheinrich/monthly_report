import os

import pandas as pd
import dill as pkl


REPORT_DATA_PATH = os.getenv("REPORT_DATA_PATH", os.getcwd())

USERS_PATH = os.path.join(REPORT_DATA_PATH, "users.pkl")
GROUPS_PATH = os.path.join(REPORT_DATA_PATH, "groups.pkl")
USAGE_PATH = os.path.join(REPORT_DATA_PATH, "usage.pkl")

def load_users():
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, "rb") as f:
            users = pkl.load(f)
        return users 
    else:
        users = pd.DataFrame(columns=["uid", "acct", "nuid", "firstName", "lastName", "email"])
        return users 


def save_users(users):
    with open(USERS_PATH, "wb") as f:
        pkl.dump(users, f)


def load_groups():
    if os.path.exists(GROUPS_PATH):
        with open(GROUPS_PATH, "rb") as f:
            groups = pkl.load(f)
        return groups
    else:
        groups = pd.DataFrame(columns=["gid", "lastName", "firstName", "email", "dept", "ngid"])
        return groups


def save_groups(groups):
    with open(GROUPS_PATH, "wb") as f:
        pkl.dump(groups, f)


def load_usage():
    if os.path.exists(USAGE_PATH):
        with open(USAGE_PATH, "rb") as f:
            usage = pkl.load(f)
        return usage
    else:
        usage = {}
        return usage


def save_usage(usage):
    with open(USAGE_PATH, "wb") as f:
        print(f"dumping to {USAGE_PATH}")
        pkl.dump(usage, f)
