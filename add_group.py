import dill as pkl
import pandas as pd
import os

import argparse

from utils import capture
from load_data import load_groups, save_groups

from add_users import get_name, get_nuid, get_email

def add_group(pkl_path, gid, dept):
    groups = load_groups(pkl_path)

    # Check if group already exists before proceeding
    if (groups['gid'] == gid).any():
        print(f'User {gid} already exists; skipping.')
    else:
        ngid = capture(f'id -u {gid}').strip()
        name = get_name(gid)
        first_name = name["first_name"]
        last_name = name["last_name"]
        email = get_email(gid)
        ngid, first_name, last_name, email, dept

        groups = pd.concat([groups, pd.DataFrame([[gid, first_name, last_name, email, dept, ngid]], columns=groups.columns)], ignore_index=True)
        groups = groups.sort_values("gid")

        save_groups(pkl_path, groups)

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("gid")
    parser.add_argument("department")
    args = parser.parse_args()

    gid = args.gid
    dept = args.department

    print('You entered ')
    print(f'gid: {gid}')
    print(f'department: {dept}')

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

    return gid, dept,


if __name__ == "__main__":
    path_to_pkl = os.getenv("REPORT_DATA_PATH", os.getcwd())
    add_group(path_to_pkl, *parse_arguments())
