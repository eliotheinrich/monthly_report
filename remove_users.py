import dill as pkl
import pandas as pd
import os

import argparse

from add_users import load_users, save_users

def remove_user(uid):
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

    users = load_users()

    # Check if group already exists before proceeding
    if not (users['uid'] == uid).any():
        print(f'User {uid} does not exist.')
    else:
        users = users[users.uid != uid]

        save_users(users)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("uid")
    args = parser.parse_args()

    uid = args.uid

    remove_user(uid)
