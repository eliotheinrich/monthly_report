import datetime
import re

import numpy as np
import dill as pkl

from utils import capture, parse_time, parse_mem, parse_storage

GROUP_PKL = "groups.pkl"
USERS_PKL = "users.pkl"
groups_data = pkl.load(open(GROUP_PKL, "rb"))

SACCT_USAGE_KEYS = ['cpuUsage', 'gpuUsage', 'reqMem', 'allocMem']
GROUPS = list(groups_data["gid"])


class Report:
    def __init__(self, months, monthly_reports):
        months = [str(m) for m in months]
        self.num_months = len(months)

        # Sort months and reports chronologically
        idx = sorted(list(range(self.num_months)), key=lambda i: months[i])
        self.months = [months[i] for i in idx]
        self.reports = [monthly_reports[i] for i in idx]

        self.all_keys = set()
        self.all_groups = set()

        for report in self.reports:
            self.all_keys = self.all_keys.union(report.keys())
            self.all_groups = self.all_groups.union(report.groups())

    def get_group_usage(self):
        total_usage_by_group = {key: {gid: [] for gid in self.all_groups} for key in self.all_keys}

        for key in self.all_keys:
            for gid in self.all_groups:
                for i in range(self.num_months):
                    total_usage_by_group[key][gid].append(self.reports[i].query(key, gid))

        return total_usage_by_group

    def get_sum_usage(self):
        total_usage = {key: [0]*self.num_months for key in self.all_keys}

        for key in self.all_keys:
            for gid in self.all_groups:
                for i in range(self.num_months):
                    total_usage[key][i] += self.reports[i].query(key, gid)

        return total_usage

    def query(self, key, idx=None):
        if idx is None:
            idx = list(range(self.num_months))

        if isinstance(idx, int):
            usage = {gid: self.reports[idx].query(key, gid) for gid in self.all_groups}
        else:
            usage = {gid: [] for gid in self.all_groups}
            for report in self.reports:
                for gid in self.all_groups:
                    usage[gid].append(report.query(key, gid))

        return usage

class MonthlyReport:
    def __init__(self, report_generators):
        self.usage = {}
        for report_generator in report_generators:
            for key, item in report_generator().items():
                self.usage[key] = item

    def keys(self):
        return self.usage.keys()

    def groups(self):
        gids = set()
        for key in self.keys():
            gids = gids.union(self.usage[key].keys())
        return gids

    def query(self, key, gid):
        if key in self.usage and gid in self.usage[key]:
            return self.usage[key][gid]
        else:
            return 0.0


SACCT_USAGE_KEYS = ['cpuUsage', 'gpuUsage', 'reqMem', 'allocMem']
class SREPORTGenerator:
    def __init__(self, start_date: datetime, end_date: datetime = None, pkl_file: str = 'usage.pkl'):
        self.start_date = start_date
        self.end_date = end_date
        if end_date is None:
            self.end_date = start_date.replace(day=28) + datetime.timedelta(days=4)
            self.end_date -= datetime.timedelta(days=self.end_date.day)

        self.start_date = str(self.start_date)
        self.end_date = str(self.end_date)

        self.pkl_filename = pkl_file
        try:
            self.pkl_data = pkl.load(open(pkl_file, "rb"))
        except EOFError:
            self.pkl_data = {}

    def __call__(self):
        usage = {key: {} for key in SACCT_USAGE_KEYS}
        for gid in GROUPS:
            if gid not in self.pkl_data:
                self.pkl_data[gid] = {}

            if self.month_has_data(gid):
                print(f"getting data for {gid} from pkl file")
                user_usage = self.get_user_usage_pkl(gid)
            else:
                print(f"getting for {gid} from sreport")
                user_usage = self.get_user_usage_sreport(gid)
                # Store new data
                self.pkl_data[gid][self.start_date] = user_usage

            for usage_key in SACCT_USAGE_KEYS:
                usage[usage_key][gid] = user_usage[usage_key]

        # Serialize data
        with open(self.pkl_filename, "wb") as f:
            print(f"dumping to {self.pkl_filename}")
            pkl.dump(self.pkl_data, f)

        return usage

    def get_user_usage_pkl(self, gid: str):
        gid_usage = self.pkl_data[gid][self.start_date]
        return gid_usage

    def get_user_usage_sreport(self, gid: str):
        cmd = f"sreport cluster AccountUtilizationByUser Accounts={gid} -T cpu,mem,gres/gpu start={self.start_date} end={self.end_date} | awk 'NR > 6 {{print $NF}}'"
        print(cmd)
        result = capture(cmd).split("\n")[:-1]

        if not result:
            cpu = 0.0
            mem = 0.0
            gpu = 0.0
        else:
            cpu = int(result[0])/60
            mem = int(result[1])/60/1024
            gpu = int(result[2])/60

        usage = {"cpuUsage": cpu, "reqMem": mem, "allocMem": mem, "gpuUsage": gpu}
        return usage

    # Checks if the database has an entry for a given group and month
    def month_has_data(self, gid: str) -> bool:
        if gid not in self.pkl_data:
            print(f"{gid} not found")
            return False

        if self.start_date not in self.pkl_data[gid]:
            print(f"{self.start_date} for {gid} not found")
            return False

        gid_usage = self.pkl_data[gid][self.start_date]
        if len(gid_usage) == 0:
            print(f"len() = 0 for {gid}")
            return False

        for key in SACCT_USAGE_KEYS:
            if np.isnan(gid_usage[key]):
                print("Found invalid val")
                return False

        return True


class SACCTReportGenerator:
    SACCT_FORMAT_WIDTHS = [ 20,      20,     20,      20,      20,        5,       20,          20,       5,          15,       50 ]
    SACCT_FORMAT_FIELDS = ['JobID', 'User', 'Group', 'State', 'Elapsed', 'NCPUS', 'Partition', 'ReqMem', 'ReqNodes', 'MaxRSS', 'AllocTres']
    SACCT_FORMAT = ','.join([f"{key}%{ind}" for key, ind in zip(SACCT_FORMAT_FIELDS, SACCT_FORMAT_WIDTHS)])

    def __init__(self, start_date: datetime, end_date: datetime = None, pkl_file: str = 'usage.pkl'):
        self.start_date = start_date
        self.end_date = end_date
        if end_date is None:
            self.end_date = start_date.replace(day=28) + datetime.timedelta(days=4)
            self.end_date -= datetime.timedelta(days=self.end_date.day)

        self.start_date = str(self.start_date)
        self.end_date = str(self.end_date)

        self.pkl_filename = pkl_file
        try:
            self.pkl_data = pkl.load(open(pkl_file, "rb"))
            print(f"Loading {pkl_file}")
        except EOFError:
            self.pkl_data = {}

        self.SACCT_QUERY_RESULT = None
        self.SACCT_MONTH = None

    def __call__(self):
        usage = {key: {} for key in SACCT_USAGE_KEYS}
        for gid in GROUPS:
            if self.month_has_data_pkl(gid):
                print(f"getting usage for {gid} from pkl file")
                user_usage = self.get_user_usage_pkl(gid)
            else:
                print(f"getting usage for {gid} from sacct")
                user_usage = self.get_user_usage_sacct(gid)
                # Store new data
                if gid not in self.pkl_data:
                    self.pkl_data[gid] = {}
                self.pkl_data[gid][self.start_date] = user_usage

            for usage_key in SACCT_USAGE_KEYS:
                usage[usage_key][gid] = user_usage[usage_key]

        # Serialize data
        with open(self.pkl_filename, "wb") as f:
            print(f"dumping to {self.pkl_filename}")
            pkl.dump(self.pkl_data, f)

        return usage

    # Converts the lines corresponding to a unique job to usage statistics
    @staticmethod
    def parse_lines(lines):
        head = lines[0]

        head_fields = SACCTReportGenerator.parse_sacct_fields(head)
        gid = head_fields['Group']
        elapsed = head_fields['Elapsed']
        ncores = head_fields['NCPUS']
        partition = head_fields['Partition']
        mem = head_fields['ReqMem']
        nodes = head_fields['ReqNodes']

        ncores = int(ncores)
        nodes = int(nodes)
        time = parse_time(elapsed)

        cpu_usage = time*ncores

        if 'gpu' in partition:
            alloc_tres = SACCTReportGenerator.parse_sacct_field(head, 'AllocTres')
            ngpus = re.search(r'gres/gpu=(\d+),', alloc_tres)
            ngpus = int(ngpus.group(1)) if ngpus else 0

            gpu_usage = time*ngpus
        else: 
            gpu_usage = 0

        total_alloc_mem = 0
        for i in range(1, len(lines)):
            max_rss = SACCTReportGenerator.parse_sacct_field(lines[i], 'MaxRSS')
            time = SACCTReportGenerator.parse_sacct_field(lines[i], 'Elapsed')
            time = parse_time(time)
            if len(max_rss) == 0:
                continue

            alloc_mem = 0
            if max_rss[-1] == "M":
                alloc_mem += float(max_rss[:-1])/1024.
            elif max_rss[-1] == "K":
                alloc_mem += float(max_rss[:-1])/1024.**2
            total_alloc_mem += alloc_mem*time

        gigabytes = parse_mem(mem, ncores, nodes)
        req_mem = time*gigabytes

        return gid, cpu_usage, gpu_usage, req_mem, total_alloc_mem

    @staticmethod
    def parse_sacct_output(output: str):
        lines = output.split('\n')

        n = 1
        job_boundaries = []

        while n < len(lines)-1:
            n += 1
            if SACCTReportGenerator.line_delimiter(lines[n]):
                if n == len(lines) - 1:
                    break

                i1 = n
                i2 = n

                while SACCTReportGenerator.parse_sacct_field(lines[i2+1], 'User') == '' and i2 != len(lines) - 2:
                    i2 += 1

                job_boundaries.append((i1, i2+1))

        jobs = []
        for (i,j) in job_boundaries:
            jobs.append(lines[i:j])

        return jobs

    def get_all_usage_in_range_sacct(self):
        sacct_cmd = f"sacct -a -S {self.start_date} -E {self.end_date} -o \"{SACCTReportGenerator.SACCT_FORMAT}\""
        output = capture(sacct_cmd)

        jobs = SACCTReportGenerator.parse_sacct_output(output)

        usage = {gid: {key: 0. for key in SACCT_USAGE_KEYS} for gid in GROUPS}
        usage['misc'] = {key: 0. for key in SACCT_USAGE_KEYS}

        for job in jobs:
            gid, job_cpu_usage, job_gpu_usage, job_req_mem, job_alloc_mem = SACCTReportGenerator.parse_lines(job)

            if gid in GROUPS:
                key = gid
            elif gid == '':
                pass
            else:
                key = 'misc'

            key = gid if gid in GROUPS else 'misc'
            usage[key]['cpuUsage'] += job_cpu_usage
            usage[key]['gpuUsage'] += job_gpu_usage
            usage[key]['reqMem'] += job_req_mem
            usage[key]['allocMem'] += job_alloc_mem

        return usage

    @staticmethod
    def parse_sacct_field(line: str, field: str):
        i = SACCTReportGenerator.SACCT_FORMAT_FIELDS.index(field)
        w = SACCTReportGenerator.SACCT_FORMAT_WIDTHS[i]

        n = 0
        for j in range(i):
            n += SACCTReportGenerator.SACCT_FORMAT_WIDTHS[j] + 1

        return line[n:n+w].strip()

    @staticmethod
    def parse_sacct_fields(line: str):
        fields = {}

        for field in SACCTReportGenerator.SACCT_FORMAT_FIELDS:
            fields[field] = SACCTReportGenerator.parse_sacct_field(line, field)

        return fields

    # Determines if a line is a delimiter between jobs in output of sacct
    @staticmethod
    def line_delimiter(line: str) -> bool:
        if line == '':
            return True
        state = SACCTReportGenerator.parse_sacct_field(line, 'State')
        uid = SACCTReportGenerator.parse_sacct_field(line, 'User')
        return uid != '' and SACCTReportGenerator.state_valid(state)

    # PENDING, RUNNING, FAILED, or CANCELLED jobs are not included in usage reports
    @staticmethod
    def state_valid(state: str) -> bool:
        return not (state == 'PENDING' or state == 'RUNNING' or state == 'FAILED' or 'CANCELLED' in state)

    def get_user_usage_pkl(self, gid: str):
        gid_usage = self.pkl_data[gid][self.start_date]
        return gid_usage

    def month_has_data_pkl(self, gid: str) -> bool:
        if gid not in self.pkl_data:
            print(f"{gid} not found")
            return False

        if self.start_date not in self.pkl_data[gid]:
            print(f"{self.start_date} for {gid} not found")
            return False

        gid_usage = self.pkl_data[gid][self.start_date]
        if len(gid_usage) == 0:
            print(f"len() = 0 for {gid}")
            return False

        for key in SACCT_USAGE_KEYS:
            if np.isnan(gid_usage[key]):
                print("Found invalid val")
                return False

        return True

    # Using sacct, gets group's usage in a given month (the day passed in month is discarded)
    def get_user_usage_sacct(self, gid: str):
        if self.SACCT_QUERY_RESULT is None or self.SACCT_MONTH != self.start_date:
            self.SACCT_QUERY_RESULT = self.get_all_usage_in_range_sacct()
            self.SACCT_MONTH = self.start_date

        return self.SACCT_QUERY_RESULT[gid]

# -- Definitions for functions which query the SQL database and the output of sacct -- #


# Gets a dictionary mapping every uid in userInfo to their corresponding gid
def all_users():
    dataframe = pkl.load(open(USERS_PKL, "rb"))
    users = list(dataframe["uid"])
    groups = list(dataframe["gid"])

    users_by_group = {}
    for uid, gid in zip(users, groups):
        if gid not in GROUPS:
            continue

        users_by_group[uid] = gid

    return users_by_group


USER_GROUPS = all_users()


class StorageReportGenerator:
    def __init__(self, storage_reports: dict[str, str], callback):
        self.storage_reports = storage_reports
        self.callback = callback

    def __call__(self):
        usage = {key: StorageReportGenerator.load_user_storage(path) for key, path in self.storage_reports.items()}

        # Adding miscellaneous storage
        self.callback(usage)

        # Sort usage by group
        for key in usage:
            usage[key] = StorageReportGenerator.categorize_storage(usage[key])
            for gid in GROUPS:
                if gid not in usage[key]:
                    usage[key][gid] = 0

        # Return all usage, including snapshot, miscellaneous, etc.
        return usage

    @staticmethod
    def load_user_storage(filename):
        user_usage = {}
        with open(filename, 'r') as f:
            lines = f.readlines()[9:]
            for line in lines:
                if 'USR' not in line:
                    continue

                items = line.split()

                storage = parse_storage(items[-1])

                ids = items[0].split(',')
                uid = ids[0]
                if uid not in user_usage:
                    user_usage[uid] = 0
                user_usage[uid] += storage

        return user_usage

    @staticmethod
    def categorize_storage(user_storage):
        storage = {}

        for id, s in user_storage.items():
            if id in USER_GROUPS:
                key = USER_GROUPS[id]
            elif id == "snapshots":
                key = "snapshots"
            else:
                key = id

            if key not in storage:
                storage[key] = 0

            storage[key] += s

        return storage

    @staticmethod
    def user_has_storage_data(uid: str) -> bool:
        query = f"SELECT * from userStorage WHERE uid = \"{uid}\";"
        result = read_sql_query(query)
        return len(result) != 0


SNAPSHOT_REPORT = '/data/usage/snapshots'


def snapshot_callback(storage):
    # Add snapshots
    if 'dataStorage' in storage:
        with open(SNAPSHOT_REPORT, 'r') as f:
            lines = f.read().split('\n')[2:-1]

        snapshot_storage = 0
        for line in lines:
            items = line.split()

            try:
                snapshot_storage += float(items[-2]) + float(items[-1])
            except ValueError:
                pass

        storage['dataStorage']['snapshots'] = snapshot_storage

    # Mark non-users as misc in Isilon
    for key in storage:
        keys_to_delete = ['data-move', 'from_sirius_data']
        for gid in storage[key]:
            if gid.isnumeric():
                keys_to_delete.append(gid)

        for to_del in keys_to_delete:
            if to_del in storage[key]:
                val = storage[key][to_del]
                del storage[key][to_del]

                if 'misc' not in storage[key]:
                    storage[key]['misc'] = 0.0

                storage[key]['misc'] += val
