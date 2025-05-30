import dill as pkl
import pandas as pd
import os

import argparse

from utils import capture
from load_data import load_groups, save_groups, get_projects_and_owners

from add_users import get_name, get_nuid, get_email

import pwd
def user_exists(uid):
    try:
        pwd.getpwnam(uid)
        return True
    except KeyError:
        return False


def proceed():
    s = ""
    while s not in ["y", "Y", "n", "N"]: 
        s = input("Proceed? (y/n): ")
        if s == "y" or s == "Y":
            return True
        elif s == "n" or s == "N":
            return False
        else:
            print("Please enter either y or n.")


def add_group(pkl_path, gid, dept):
    groups = load_groups(pkl_path)

    if dept not in list(groups["dept"]):
        print(f"The provided department {dept} does not already exist. Still add group?")
        if not proceed():
            print("Exiting.")
            return

    # Check if group already exists before proceeding
    if (groups["gid"] == gid).any():
        print(f"User {gid} already exists; skipping.")
    else:
        ngid = capture(f'id -u {gid}').strip()
        name = get_name(gid)
        first_name = name["first_name"]
        last_name = name["last_name"]
        email = get_email(gid)
        _, project_owners = get_projects_and_owners()
        projects = ', '.join(project_owners[gid])

        groups = pd.concat([groups, pd.DataFrame([[gid, projects, first_name, last_name, email, dept, ngid]], columns=groups.columns)], ignore_index=True)
        groups = groups.sort_values("gid")

        save_groups(pkl_path, groups)


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("gid")
    parser.add_argument("department")
    args = parser.parse_args()

    gid = args.gid
    dept = args.department

    if not user_exists(gid):
        print(f"User {gid} does not exist. Exiting.")
        quit()

    print("You entered ")
    print(f"gid: {gid}")
    print(f"department: {dept}")

    if proceed():
        return gid, dept,
    else:
        print("Exiting.")
        quit()


if __name__ == "__main__":
    path_to_pkl = os.getenv("REPORT_DATA_PATH", os.getcwd())
    add_group(path_to_pkl, *parse_arguments())
