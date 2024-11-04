import dill as pkl
import pandas as pd

import argparse

def remove_group(gid):
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

    with open("users.pkl", "rb") as f:
        groups = pkl.load(f)

    if not (groups['gid'] == gid).any():
        print(f'User {gid} does not exist.')
    else:
        groups = groups[groups.gid != gid]

        with open("users.pkl", "wb") as f:
            pkl.dump(groups, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("gid")
    args = parser.parse_args()

    gid = args.gid

    remove_group(gid)
