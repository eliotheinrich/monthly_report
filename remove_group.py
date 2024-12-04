import dill as pkl
import pandas as pd
import os

import argparse

def remove_group(groups_filename, gid):
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

    # Check if group already exists before proceeding
    with open(groups_filename, "rb") as f:
        groups = pkl.load(f)

    if not (groups['gid'] == gid).any():
        print(f'User {gid} does not exist.')
    else:
        groups = groups[groups.gid != gid]

        with open(groups_filename, "wb") as f:
            pkl.dump(groups, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("gid")
    args = parser.parse_args()

    gid = args.gid

    data_path = os.getenv("REPORT_DATA_PATH", os.getcwd())
    groups_filename = os.path.join(data_path, "groups.pkl")
    remove_group(groups_filename, gid)
