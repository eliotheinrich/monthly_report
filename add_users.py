import dill as pkl
import pandas as pd
import os
import argparse

from utils import capture

from load_data import load_groups, load_users, save_users


def user_exists(uid: str):
    s = capture(f'getent passwd {uid}').strip()
    return s != ''


def get_name(uid: str):
    s = capture(f'getent passwd {uid}').strip()
    name = s.split(':')[4]
    first_name = name.split()[0]
    last_name = name.split()[-1]

    return {'first_name': first_name, 'last_name': last_name}


def get_nuid(uid: str):
    return capture(f'id -u {uid}').strip()


def get_email(uid: str):
    return uid + '@bc.edu'


def update_users(verbose: bool):
    unknown_ngids = set()

    groups = load_groups()
    users = load_users()

    sacctmgr_output = capture('sacctmgr list user -Pn').strip().split('\n')
    andromeda_users = []
    for line in sacctmgr_output:
        uid, acct, _ = line.split('|')
        if not (users['uid'] == uid).any():
            if user_exists(uid):
                new_user = {'uid': uid, 'acct': acct, 'nuid': get_nuid(uid), 'email': get_email(uid), **get_name(uid)}
                andromeda_users.append(new_user)
            else:
                if verbose:
                    print(f"User {uid} exists in slurmdb but not posix permissions.")


    # Updating userInfo
    def add_user(user_info):
        nonlocal users
        uid = user_info['uid']

        # Check if user already exists before proceeding
        if (users['uid'] == uid).any():
            return
        else:
            if verbose:
                print(f"Adding {uid}")

        acct = user_info['acct']
        nuid = user_info['nuid']
        first_name = user_info['first_name']
        last_name = user_info['last_name']
        email = user_info['email']

        users = pd.concat([users, pd.DataFrame([[uid, acct, nuid, first_name, last_name, email]], columns=users.columns)], ignore_index=True)
        users = users.sort_values("uid")


    for user_info in andromeda_users:
        add_user(user_info)

    save_users(users)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    verbose = args.verbose

    update_users(verbose)
