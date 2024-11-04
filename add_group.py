import dill as pkl
import pandas as pd

import argparse

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

def add_group():
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

    # Check if group already exists before proceeding

    with open("groups.pkl", "rb") as f:
        groups = pkl.load(f)

    if (groups['gid'] == gid).any():
        print(f'User {gid} already exists; skipping.')
    else:
        groups = pd.concat([groups, pd.DataFrame([[gid, last_name, first_name, email, dept, ngid]], columns=groups.columns)], ignore_index=True)
        groups = groups.sort_values("gid")

        with open("groups.pkl", "wb") as f:
            pkl.dump(groups, f)

if __name__ == "__main__":
    add_group()
