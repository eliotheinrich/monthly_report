import dill as pkl
import pandas as pd
import os

import argparse

def add_group(groups_filename, gid, ngid, first_name, last_name, email, dept):
    # Check if group already exists before proceeding

    with open(groups_filename, "rb") as f:
        groups = pkl.load(f)

    if (groups['gid'] == gid).any():
        print(f'User {gid} already exists; skipping.')
    else:
        groups = pd.concat([groups, pd.DataFrame([[gid, last_name, first_name, email, dept, ngid]], columns=groups.columns)], ignore_index=True)
        groups = groups.sort_values("gid")

        with open(groups_filename, "wb") as f:
            pkl.dump(groups, f)

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("gid")
    parser.add_argument("ngid")
    parser.add_argument("firstName")
    parser.add_argument("lastName")
    parser.add_argument("email")
    parser.add_argument("department")
    args = parser.parse_args()

    gid = args.gid
    ngid = args.ngid
    first_name = args.firstName
    last_name = args.lastName
    email = args.email
    dept = args.department

    print('You entered ')
    print(f'gid: {gid}')
    print(f'ngid: {ngid}')
    print(f'first name: {first_name}')
    print(f'last name: {last_name}')
    print(f'email: {email}')
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

    return gid, ngid, first_name, last_name, email, dept


if __name__ == "__main__":
    data_path = os.getenv("REPORT_DATA_PATH", os.getcwd())
    groups_filename = os.path.join(data_path, "groups.pkl")
    add_group(groups_filename, *parse_arguments())
