from report_generator import *
from report_plots import *
from add_users import update_users
from group_report import make_group_report
from user_report import make_user_report

import sys
import os
import time

import argparse
from dateutil import relativedelta

from utils import parse_date, set_verbosity

from load_data import Context


# -- Running functions which collect all usage data over the last NUM_MONTHS starting from THIS_MONTH ----- #
# -- Automatically detects if data exists in the SQL database and uses it if so --------------------------- #
# -- Otherwise, get new data using sacct ------------------------------------------------------------------ #

# Generate report for the NUM_MONTHS preceeding THIS_MONTH
# I.e. if NUM_MONTHS = 13 and THIS_MONTH = "2023-05-01", collects usage data for the period between Apr 2022 and Apr 2023.

# Parsing command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("date")
parser.add_argument("--num-months", nargs=1, default=[13])
parser.add_argument("--output-extension", nargs=1, default=["svg"])
parser.add_argument("--isilon-report-path", nargs=1, default=[None])
parser.add_argument("-i", "--insert", action="store_false")
parser.add_argument("-o", "--output-files", action="store_false")
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("-u", "--user", action="store_false")
parser.add_argument("-d", "--directory")
args = parser.parse_args()

INSERT = args.insert
OUTPUT_FILES = args.output_files
OUTPUT_EXTENSION = args.output_extension[0]
NUM_MONTHS = int(args.num_months[0])
THIS_MONTH = parse_date(args.date)
FIRST_MONTH = THIS_MONTH - relativedelta.relativedelta(months=NUM_MONTHS)
VERBOSITY = args.verbose
DIRECTORY = args.directory

set_verbosity(VERBOSITY)


context = Context(verbosity = VERBOSITY, insert_data = INSERT, path_to_quota = "/m31/reps/wekafs.qta", path_to_pkl = os.getenv("REPORT_DATA_PATH", os.getcwd()))

print(f"Generating report for {FIRST_MONTH} through {THIS_MONTH}.")
if OUTPUT_FILES:
    print(f"Generating output files: {OUTPUT_FILES}. File format: .{OUTPUT_EXTENSION}")
else:
    print(f"Generating output files: {OUTPUT_FILES}.")

print(f"Inserting new data into database: {INSERT}")

if DIRECTORY is not None:
    try:
        os.mkdir(DIRECTORY)
    except FileExistsError as e:
        pass

months = [THIS_MONTH - relativedelta.relativedelta(months=i+1) for i in range(NUM_MONTHS)]
monthly_reports = []

t0 = time.time()
for n,month in enumerate(months):
    report_generators = [SREPORTGenerator(context, month), StorageReportGenerator(context), GlobalReportGenerator(context, month)]
    monthly_report = MonthlyReport(report_generators)
    monthly_reports.append(monthly_report)

report = Report(context, months, monthly_reports)

t1 = time.time()
print(f"Querying usage data took {(t1 - t0):.2f} seconds.")

#if INSERT:
#    report.insert('monthlyUsage')

# Process report
group_keys = ["homeStorage", "scratchStorage", "projectStorage", "cpuUsage", "gpuUsage", "reqMem"]
group_usage = report.get_group_usage(group_keys)
total_group_usage = {key: {gid: sum(group_usage[key][gid]) for gid in context.gids} for key in SACCT_USAGE_KEYS}
sum_usage = report.get_sum_usage(group_keys)

home_storage = report.query_group_usage("homeStorage", idx=-1)
scratch_storage = report.query_group_usage("scratchStorage", idx=-1)
project_storage = report.query_group_usage("projectStorage", idx=-1)

total_storage = {}
for storage in [home_storage, scratch_storage, project_storage]:
    for id,val in storage.items():
        if id not in total_storage:
            total_storage[id] = 0
        total_storage[id] += val


# If we are not generating files for the report, exit now.
if not OUTPUT_FILES:
    sys.exit(0)

if INSERT:
    update_users(context)

TOTAL_STORAGE_SPACE = 1.5*(1024)**2 # 1.5 PB

plt.rcParams['font.size'] = 25

plot_storage_by_group(context, home_storage, cutoff=11, title=f"/home/ storage", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY, f="home")
plot_storage_by_group(context, scratch_storage, cutoff=11, title=f"/scratch/ storage", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
plot_storage_by_group(context, project_storage, cutoff=11, title=f"/projects/ storage", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
plot_storage_by_department(context, home_storage, title=f"/home/ storage usage by department", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY, f="home")
plot_storage_by_department(context, scratch_storage, title=f"/scratch/ storage usage by department", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
plot_storage_by_department(context, project_storage, title=f"/projects/ storage usage by department", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
plot_storage_by_group_piechart(context, total_storage, cutoff=7, total_storage=TOTAL_STORAGE_SPACE, title=f"Adromeda total storage", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)

plot_usage_by_department(context, total_group_usage["cpuUsage"], start_date=report.months[0], end_date=report.months[-1], title="CPU Usage by department", xlabel="CPU hours used", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
plot_usage_by_department(context, total_group_usage["gpuUsage"], start_date=report.months[0], end_date=report.months[-1], title="GPU Usage by department", xlabel="GPU hours used", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
plot_usage_by_group(context, total_group_usage["cpuUsage"], start_date=report.months[0], end_date=report.months[-1], title=f"CPU time used", xlabel = r"CPU hours used", threshold = 15, output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
plot_usage_by_group(context, total_group_usage["gpuUsage"], start_date=report.months[0], end_date=report.months[-1], title=f"GPU time used", xlabel = r"GPU hours used", threshold = 15, output_extension=OUTPUT_EXTENSION, directory=DIRECTORY, f="GPU")
plot_usage_by_group(context, total_group_usage["reqMem"], start_date=report.months[0], end_date=report.months[-1], title=f"MEM requested", xlabel=r"GB$\cdot$hrs used", threshold = 15, output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)

plot_yearly_usage(sum_usage["cpuUsage"], months=report.months, title="CPU Usage - All Users", ylabel = "CPU Hours", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
plot_yearly_usage(sum_usage["gpuUsage"], months=report.months, title="GPU Usage - All Users", ylabel = "GPU Hours", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY, f="GPU")
plot_yearly_usage(sum_usage["reqMem"], months=report.months, title="MEM Usage - All Users", ylabel = r"GB$\cdot$hours", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)

colors = ["C3", "C0", "C1", "C2"]
cpu_utilization = [report.query(key) for key in ["cpuAlloc", "cpuIdle", "cpuDown", "cpuPLNDDown"]]
cpu_labels = ["CPU allocated", "CPU idle", "CPU down", "CPU planned down"]
plot_utilization(cpu_utilization, cpu_labels, colors, months=report.months, title="CPU Utilization", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)
gpu_utilization = [report.query(key) for key in ["gpuAlloc", "gpuIdle", "gpuDown", "gpuPLNDDown"]]
gpu_labels = ["GPU allocated", "GPU idle", "GPU down", "GPU planned down"]
plot_utilization(gpu_utilization, gpu_labels, colors, months=report.months, title="GPU Utilization", output_extension=OUTPUT_EXTENSION, directory=DIRECTORY)

make_report_sheet(context, report, group_keys, directory=DIRECTORY)
make_user_report(context, date_label(THIS_MONTH), directory=DIRECTORY)
make_group_report(context, date_label(THIS_MONTH), directory=DIRECTORY)
