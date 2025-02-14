import dill as pkl
import pandas as pd
import os
import argparse

from utils import capture

from load_data import Context


def user_exists(uid: str):
    s = capture(f"getent passwd {uid}").strip()
    return s != ""


def get_name(uid: str):
    s = capture(f"getent passwd {uid}").strip()
    name = s.split(":")[4]
    first_name = name.split()[0]
    last_name = name.split()[-1]

    return {"first_name": first_name, "last_name": last_name}


def get_nuid(uid: str):
    return capture(f"id -u {uid}").strip()


def get_email(uid: str):
    return uid + "@bc.edu"


def get_project_owner(context: Context, project: str):
    if project in context.projects:
        return context.projects[project]
    else:
        return project


def update_users(context: Context):
    unknown_ngids = set()

    sacctmgr_output = capture("sacctmgr list user -Pn").strip().split("\n")
    andromeda_users = []
    for line in sacctmgr_output:
        uid, project, _ = line.split("|")
        if uid not in context.uids:
            if user_exists(uid):
                new_user = {"uid": uid, "project": project, "project_owner": get_project_owner(context, project), "nuid": get_nuid(uid), "email": get_email(uid), **get_name(uid)}
                andromeda_users.append(new_user)
            else:
                if context.verbose:
                    print(f"User {uid} exists in slurmdb but not posix permissions.")

    # Updating userInfo
    def add_user(users, user_info, context):
        uid = user_info["uid"]

        # Check if user already exists before proceeding
        if uid in list(users["uid"]):
            return
        else:
            if context.verbose:
                print(f"Adding {uid}")

        project = user_info["project"]
        project_owner = user_info["project_owner"]
        nuid = user_info["nuid"]
        first_name = user_info["first_name"]
        last_name = user_info["last_name"]
        email = user_info["email"]

        users = pd.concat([users, pd.DataFrame([[uid, project, project_owner, nuid, first_name, last_name, email]], columns=users.columns)], ignore_index=True)
        return users.sort_values("uid")

    users = context.users
    for user_info in andromeda_users:
        users = add_user(users, user_info, context)
    context.save_users(users)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    verbose = args.verbose

    context = Context(verbosity = verbose, path_to_pkl = os.getenv("REPORT_DATA_PATH", os.getcwd()))

    update_users(context)
