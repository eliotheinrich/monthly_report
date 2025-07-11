import os

import pandas as pd
import dill as pkl

from utils import capture


def load_users(pkl_path):
    file_path = os.path.join(pkl_path, "users.pkl")
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            users = pkl.load(f)
        return users 
    else:
        users = pd.DataFrame(columns=["uid", "nuid", "projects", "gid", "firstName", "lastName", "email"])
        return users 


def save_users(pkl_path, users):
    file_path = os.path.join(pkl_path, "users.pkl")
    with open(file_path, "wb") as f:
        pkl.dump(users, f)


def load_groups(pkl_path):
    file_path = os.path.join(pkl_path, "groups.pkl")
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            groups = pkl.load(f)
        return groups
    else:
        groups = pd.DataFrame(columns=["gid", "projects", "firstName", "lastName", "email", "dept", "ngid"])
        return groups


def save_groups(pkl_path, groups):
    file_path = os.path.join(pkl_path, "groups.pkl")
    with open(file_path, "wb") as f:
        pkl.dump(groups, f)


def load_usage(pkl_path):
    file_path = os.path.join(pkl_path, "usage.pkl")
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            usage = pkl.load(f)
        return usage
    else:
        usage = {}
        return usage


def save_usage(pkl_path, usage):
    file_path = os.path.join(pkl_path, "usage.pkl")
    with open(file_path, "wb") as f:
        pkl.dump(usage, f)


def get_projects_and_owners():
    root_directories = ["/projects/", "/nbu/"]
    ignored = {"fmp2", "dasarat", "sobled"}

    projects = {}
    project_owners = {}

    for dir in root_directories:
        command = f"ls -l1 {dir}"
        output = capture(command).strip().split("\n")[1:]

        for line in output:
            data = line.split()
            owner = data[2]
            if owner in ignored:
                continue
            project_name = data[-1]
            projects[project_name] = owner
            if owner not in project_owners:
                project_owners[owner] = []

            project_owners[owner].append(project_name)

    return projects, project_owners


class Context:
    def __init__(self, path_to_pkl, verbosity=False, insert_data=False, path_to_quota=None):
        self.verbose = verbosity

        self.path_to_quota = path_to_quota
        self.path_to_pkl = path_to_pkl

        self.groups = load_groups(path_to_pkl)
        self.gids = list(self.groups["gid"])
        self.users = load_users(path_to_pkl)
        self.uids = list(self.users["uid"])

        self.projects, self.project_owners = get_projects_and_owners()

        self.insert = insert_data

        ignored = ["root", "shibh", "parif", "johnchris", "gregas"]
        for owner in self.project_owners:
            if owner not in self.gids and owner not in ignored:
                raise RuntimeError(f"The PI {owner} not found. Add them with `python add_group.py {owner} DEPARTMENT` and run again.")


    def get_groups(self):
        return self.gids


    def get_group_name(self, gid: str) -> str:
        if gid == "":
            return "Unknown"
        if gid == "misc":
            return "Miscellaneous"
        if gid in self.gids:
            query_result = self.groups.query(f"gid == \"{gid}\"")
            first_name = query_result["firstName"].iloc[0]
            last_name = query_result["lastName"].iloc[0]
            return first_name[0] + ". " + last_name
        else:
            return gid


    def get_project_owner(self, id):
        if id in self.uids:
            query_result = self.users.query(f"uid == \"{id}\"")
            gid = query_result["gid"].iloc[0]
            return gid
        else:
            return self.projects[id]


    def load_usage(self):
        return load_usage(self.path_to_pkl)


    def save_usage(self, usage):
        save_usage(self.path_to_pkl, usage)


    def save_users(self, users):
        save_users(self.path_to_pkl, users)


    def save_groups(self, groups):
        save_groups(self.path_to_pkl, groups)


    def get_department(self, gid: str) -> str:
        query_result = self.groups.query(f"gid == \"{gid}\"")
        return query_result["dept"].iloc[0]


    def get_label(self, label: str) -> str:
        if label in self.gids:
            return self.get_group_name(label)
        if label == "misc":
            return "Miscellaneous"
        if label == "snapshots":
            return "Snapshots"
        
        return label


