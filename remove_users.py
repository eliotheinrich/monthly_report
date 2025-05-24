import dill as pkl
import pandas as pd
import os

import argparse

from load_data import load_users, save_users

def remove_user(pkl_path, uid):
    print(f'Deleting {uid}. ')

    s = ''
    while s not in ['y', 'Y', 'n', 'N']: 
        s = input('Is this correct? (y/n): ')
        if s == 'y' or s == 'Y':
            break
        elif s == 'n' or s == 'N':
            print('Please try again.')
            return
        else:
            print('Please enter either y or n.')

    users = load_users(pkl_path)

    # Check if group already exists before proceeding
    if not (users['uid'] == uid).any():
        print(f'User {uid} does not exist.')
    else:
        users = users[users.uid != uid]

        save_users(pkl_path, users)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("uid")
    args = parser.parse_args()

    uid = args.uid

    pkl_path = os.getenv("REPORT_DATA_PATH", os.getcwd())
    remove_user(pkl_path, uid)
