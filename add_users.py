import dill as pkl
import pandas as pd

from accounting_utils import capture

def update_users(groups_pkl_file="groups.pkl", users_pkl_file="users.pkl"):
    unknown_ngids = set()

    with open(groups_pkl_file, "rb") as f:
        groups = pkl.load(f)

    with open(users_pkl_file, "rb") as f:
        users = pkl.load(f)

    def user_exists(uid):
        s = capture(f'getent passwd {uid}')
        return s != ''

    def get_name(uid):
        s = capture(f'getent passwd {uid}')
        name = s.split(':')[4]
        first_name = name.split()[0]
        last_name = name.split()[-1]

        return {'first_name': first_name, 'last_name': last_name}

    def gid_lookup(ngid):
        nonlocal groups
        query_result = groups.loc[groups['ngid'] == ngid]
        if len(query_result) > 0:
            print(f'{ngid} has group {query_result}')
            return query_result.iloc[0]['gid']
        else:
            print(f'{ngid} cannot be identified.')
            return None 

    def get_id(uid):
        nuid = capture('id -u ' + uid).strip()
        ngid = capture('id -g ' + uid).strip()
        gid_output = capture('id -gn ' + uid).strip().split('\n')
        if len(gid_output) == 2:
            print(f'Looking up {uid} with ngid {ngid}')
            ngid = gid_output[1]
            gid = gid_lookup(ngid)
            if gid is None:
                print(f'Could not find group corresponding to gid {ngid}')
                unknown_ngids.add(ngid)
                
        elif len(gid_output) == 1:
            gid = gid_output[0]

        return {'nuid': nuid, 'ngid': ngid, 'gid': gid}

    def get_email(uid):
        return {'email': uid + '@bc.edu'}

    def get_user_info(uid):
        t = {'uid': uid}
        return {**t, **get_name(uid), **get_id(uid), **get_email(uid)}

# Collect user information from Andromeda based on the contents of /data/
# Some users (sysadmins, test accounts, etc) are filtered

    uids = capture('ls /data/').split()
    uids = [user.strip().replace('/', '') for user in uids]
    ignore_uids = ['admin', 'swadmin', 'jem', 'parif', 'dilascij', 'salazajg']
    ignore_gids = ['fmp']

    andromeda_users = {}
    for uid in uids:
        if user_exists(uid) and uid not in ignore_uids:
            id = get_id(uid)
            if id['gid'] not in ignore_gids:
                andromeda_users[uid] = get_user_info(uid)
                continue

        ignore_uids.append(uid)

    # Updating userInfo
    n = 0
    def add_user(user_info):
        nonlocal users
        nonlocal n
        uid = user_info['uid']

        # Check if user already exists before proceeding
        if (users['uid'] == uid).any():
            return
        else:
            print(f"({n}) Adding {uid}")
            n += 1

        gid = user_info['gid']
        nuid = user_info['nuid']
        first_name = user_info['first_name']
        last_name = user_info['last_name']
        email = user_info['email']
        bc = 'y'
        active = 'y'

        users = pd.concat([users, pd.DataFrame([[uid, gid, nuid, first_name, last_name, email, bc, active]], columns=users.columns)], ignore_index=True)
        users = users.sort_values("uid")

    for uid, user_info in andromeda_users.items():
        ngid = user_info['ngid']
        if ngid in unknown_ngids:
            print(f"Don't know what to do with {uid}")
        else:
            add_user(user_info)

    with open(users_pkl_file, "wb") as f:
        pkl.dump(users, f)

if __name__ == "__main__":
    update_users()
