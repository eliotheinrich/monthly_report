import datetime
import re
import os

import numpy as np
import dill as pkl

from utils import capture, parse_time, parse_mem, parse_storage

from load_data import Context

SACCT_USAGE_KEYS = ["cpuUsage", "gpuUsage", "reqMem"]

class Report:
    def __init__(self, context, months, monthly_reports):
        self.context = context

        months = [str(m) for m in months]
        self.num_months = len(months)

        # Sort months and reports chronologically
        idx = sorted(list(range(self.num_months)), key=lambda i: months[i])
        self.months = [months[i] for i in idx]
        self.reports = [monthly_reports[i] for i in idx]

        self.all_keys = set()
        self.all_groups = context.get_groups()

        for report in self.reports:
            self.all_keys = self.all_keys.union(report.keys())

    def get_group_usage(self, keys):
        total_usage_by_group = {key: {gid: [] for gid in self.all_groups} for key in keys}

        for key in keys:
            for gid in self.all_groups:
                for i in range(self.num_months):
                    total_usage_by_group[key][gid].append(self.reports[i].query(key, gid))

        return total_usage_by_group

    def get_sum_usage(self, keys):
        total_usage = {key: [0]*self.num_months for key in keys}

        for key in keys:
            for i in range(self.num_months):
                for gid in self.all_groups:
                    total_usage[key][i] += self.reports[i].query(key, gid)

        return total_usage

    def query(self, key, idx=None):
        if idx is None:
            idx = list(range(self.num_months))

        usage = [self.reports[i].query(key) for i in idx]

        return usage


    def query_group_usage(self, key, idx=None):
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

    def query(self, key, gid=None):
        if gid is None:
            if key in self.usage:
                return self.usage[key]

        if key in self.usage and gid in self.usage[key]:
            return self.usage[key][gid]
        else:
            return 0.0


class GlobalReportGenerator:
    def __init__(self, context: Context, start_date: datetime, end_date: datetime = None):
        self.context = context 

        self.start_date = start_date
        self.end_date = end_date
        if end_date is None:
            self.end_date = start_date.replace(day=28) + datetime.timedelta(days=4)
            self.end_date -= datetime.timedelta(days=self.end_date.day)


    def __call__(self):
        cmd = f"sreport cluster utilization start={self.start_date} end={self.end_date} -t percent -T ALL --parsable2"
        output = capture(cmd).strip().split("\n")[5:]

        def parse_percent(s):
            return float(s.replace("%", ""))
            
        cpu_idx = next((i for i, x in enumerate(output) if x.split("|")[1] == "cpu"), -1)
        gpu_idx = next((i for i, x in enumerate(output) if x.split("|")[1] == "gres/gpu"), -1)

        if cpu_idx == -1:
            raise RuntimeError(f"Could not get CPU usage from output of {cmd}.")
        if gpu_idx == -1:
            raise RuntimeError(f"Could not get GPU usage from output of {cmd}.")

        cpu_utilization = output[cpu_idx].split("|")
        gpu_utilization = output[gpu_idx].split("|")
        usage = {
            "cpuAlloc":    parse_percent(cpu_utilization[2]),
            "cpuDown":     parse_percent(cpu_utilization[3]),
            "cpuPLNDDown": parse_percent(cpu_utilization[4]),
            "cpuIdle":     parse_percent(cpu_utilization[5]),

            "gpuAlloc":    parse_percent(gpu_utilization[2]),
            "gpuDown":     parse_percent(gpu_utilization[3]),
            "gpuPLNDDown": parse_percent(gpu_utilization[4]),
            "gpuIdle":     parse_percent(gpu_utilization[5]),
        }

        return usage


class SREPORTGenerator:
    def __init__(self, context: Context, start_date: datetime, end_date: datetime = None):
        self.start_date = start_date
        self.end_date = end_date
        if end_date is None:
            self.end_date = start_date.replace(day=28) + datetime.timedelta(days=4)
            self.end_date -= datetime.timedelta(days=self.end_date.day)

        self.start_date = str(self.start_date)
        self.end_date = str(self.end_date)

        self.pkl_data = context.load_usage()
        self.context = context

    def __call__(self):
        usage = {key: {} for key in SACCT_USAGE_KEYS}
        for gid in self.context.gids:
            if gid not in self.pkl_data:
                self.pkl_data[gid] = {}

            if self.month_has_data(gid):
                if self.context.verbose:
                    print(f"getting data for {gid} from pkl file")
                user_usage = self.get_user_usage_pkl(gid)
            else:
                if self.context.verbose:
                    print(f"getting for {gid} from sreport")
                user_usage = self.get_user_usage_sreport(gid)

                # Store new data
                self.pkl_data[gid][self.start_date] = user_usage

            for usage_key in SACCT_USAGE_KEYS:
                usage[usage_key][gid] = user_usage[usage_key]

        # Serialize data
        if self.context.insert:
            self.context.save_usage(self.pkl_data)
        
        return usage

    def get_user_usage_pkl(self, gid: str):
        gid_usage = self.pkl_data[gid][self.start_date]
        return gid_usage

    def get_project_usage_sreport(self, project: str):
        cmd = f"sreport cluster AccountUtilizationByUser Accounts={project} -T cpu,mem,gres/gpu start={self.start_date} end={self.end_date} | awk 'NR > 6 {{print $NF}}'"
        if self.context.verbose:
            print(cmd)
        result = capture(cmd).strip().split("\n")

        if result == ['']:
            cpu = 0.0
            mem = 0.0
            gpu = 0.0
        else:
            cpu = int(result[0])/60
            mem = int(result[1])/60/1024
            gpu = int(result[2])/60

        usage = {"cpuUsage": cpu, "reqMem": mem, "gpuUsage": gpu}
        return usage


    def get_user_usage_sreport(self, gid: str):
        usage = {key: 0.0 for key in SACCT_USAGE_KEYS}
        if gid in self.context.project_owners:
            for project in self.context.project_owners[gid]:
                project_usage = self.get_project_usage_sreport(project)
                for key, val in project_usage.items():
                    usage[key] += val

        return usage


    # Checks if the database has an entry for a given group and month
    def month_has_data(self, gid: str) -> bool:
        if gid not in self.pkl_data:
            if self.context.verbose:
                print(f"{gid} not found")
            return False

        if self.start_date not in self.pkl_data[gid]:
            if self.context.verbose:
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


def default_callback(usage):
    return


class StorageReportGenerator:
    def __init__(self, context: Context, callback=default_callback):
        self.callback = callback
        self.context = context

    def __call__(self):
        def to_gigabytes(amount, suffix):
            amount = float(amount)
            if suffix == "TB":
                return amount * 1024
            elif suffix == "GB":
                return amount
            elif suffix == "MB":
                return amount / 1024
            elif suffix == "KB":
                return amount / 1024**2
            elif suffix == "B":
                return amount / 1024**3
            else:
                raise RuntimeException(f"Error parsing {amount} {suffix} into GB.")

        usage = {"homeStorage": {}, "scratchStorage": {}, "projectStorage": {}}
        storage_type_map = {"home": "homeStorage", "scratch": "scratchStorage", "projects": "projectStorage"}

        output = capture(f"tail -n +0 {self.context.path_to_quota}").strip().split('\n')[1:]
        for line in output:
            line_items = line.split()

            storage_type, line_user = line_items[0].split(":/")
            if line_user in self.context.uids or line_user in self.context.projects:
                project_owner = self.context.get_project_owner(line_user)
                if project_owner in self.context.gids:
                    key = storage_type_map[storage_type]
                    if project_owner not in usage[key]:
                        usage[key][project_owner] = 0.0

                    size = to_gigabytes(line_items[1], line_items[2])
                    usage[key][project_owner] += size

        # Adding miscellaneous storage
        self.callback(usage)

        # Return all usage, including snapshot, miscellaneous, etc.
        return usage
