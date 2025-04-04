import dill as pkl
import pandas as pd
import os

import argparse

from add_group import load_groups, save_groups

def remove_group(pkl_path, gid):
    print(f'Deleting {gid}. ')

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

    groups = load_groups(pkl_path)

    # Check if group already exists before proceeding
    if not (groups['gid'] == gid).any():
        print(f'User {gid} does not exist.')
    else:
        groups = groups[groups.gid != gid]

        save_groups(pkl_path, groups)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("gid")
    args = parser.parse_args()

    gid = args.gid

    pkl_path = os.getenv("REPORT_DATA_PATH", os.getcwd())
    remove_group(pkl_path, gid)
