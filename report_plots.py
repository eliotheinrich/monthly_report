# -- Generates usage plots for report -- #

from accounting_utils import *
from report_generator import GROUPS, SACCT_USAGE_KEYS
from report_generator import groups_data

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib as mpl

import numpy as np

# Gets the full name of a group
def get_user_name(gid: str) -> str:
    if gid == '':
        return 'Unknown'
    if gid == 'misc':
        return 'Miscellaneous'
    if gid == 'snapshots':
        return 'Snapshots'
    if gid in GROUPS:
        query_result = groups_data.query(f"gid == \"{gid}\"")
        first_name = query_result["firstName"].iloc[0]
        last_name = query_result["lastName"].iloc[0]
        return first_name[0] + ". " + last_name
    else:
        return gid

def get_label(label: str) -> str:
    if label in GROUPS:
        return GROUP_NAMES[label]
    if label == 'misc':
        return 'Miscellaneous'
    if label == 'snapshots':
        return 'Snapshots'
    
    return label

# Gets the department of a group 
def get_department(gid: str) -> str:
    if gid in GROUPS:
        query_result = groups_data.query(f"gid == \"{gid}\"")
        return query_result["dept"].iloc[0]

    return "Miscellaneous"
        

MONTHS = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
GROUP_NAMES = {gid: get_user_name(gid) for gid in GROUPS}

def date_label(date):
    d = str(date)
    return MONTHS[int(d[5:7])] + '-' + d[2:4]

plt.rcParams['font.size'] = 25


def plot_usage_by_group(group_usage, start_date, end_date, alloc=None, title=None, xlabel=None, threshold=0, directory=None, output_extension="png"):
    if directory is None:
        directory = ""
    else:
        if directory[-1] != "/":
            directory += "/"
    fig, ax = plt.subplots(figsize=(20,12))

    users, time = zip(*[(k, v) for k,v in group_usage.items() if v > threshold])
    sorted_inds = np.flip(np.argsort(time))
    users, time = np.array(users)[sorted_inds], np.array(time)[sorted_inds]

    ax.barh([get_label(gid) for gid in users], time, color='orange', label='Requested')
    if alloc is not None:
        users, alloc_time = zip(*[(k, v) for k,v in alloc.items() if v > threshold])
        sorted_inds = np.flip(np.argsort(alloc_time))
        users, alloc_time = np.array(users)[sorted_inds], np.array(alloc_time)[sorted_inds]
        ax.barh([get_label(gid) for gid in users], alloc_time, color='C0', label='Allocated')
        
    plt.yticks(rotation=0)
    ax.set_xlim(0, max(time)*1.2)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: str(int(x/1000)) + 'k'))
    plt.title(f'{date_label(start_date)} - {date_label(end_date)}', y=1.0, pad=30)
    if title is not None:
        plt.suptitle(title)
    if xlabel is not None:
        plt.xlabel(xlabel)

    # Hide axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)


    # Add gridlines
    for tick in ax.get_xticks():
        plt.axvline(tick, linewidth=0.25, color='k', zorder=0)

    # Hide ticks and remove bottom ytick corresponding to 0 hours
    ax.tick_params(axis='both', length=0)
    ax.set_xticks(ax.get_xticks()[1:])

    if alloc is not None:
        plt.legend()

    plt.savefig(directory + title + '.' + output_extension, bbox_inches='tight')
    plt.show()

def plot_yearly_usage(
        total_usage, 
        months,
        alloc = None,
        title: str = None,
        ylabel: str = None,
        max_usage: int = None,
        directory: str = None,
        output_extension="png"
    ):

    if directory is None:
        directory = ""
    else:
        if directory[-1] != "/":
            directory += "/"

    num_months = len(months)
    start_date = months[0]
    end_date = months[-1]
    
    _, ax = plt.subplots(figsize=(12, 8))
    xticks = list(range(0, num_months))

    legend_items = []
    
    plt.plot(xticks, total_usage, color='orange')
    legend_items.append((mpl.patches.Rectangle([0,0],0,0, color='orange'), 'Requested'))
    plt.fill_between(xticks, total_usage, color='orange')
 
    if alloc is not None:
        plt.plot(xticks, alloc, color='C0', label='Allocated', linewidth=3.0)
        legend_items.append((mpl.patches.Rectangle([0,0],0,0, color='C0'), 'Allocated'))
        plt.fill_between(xticks, alloc, color='C0')
 
    plt.suptitle(title)
    plt.title(f'{date_label(start_date)} - {date_label(end_date)}')


    # Format x-axis
    #ax.set_xlim(start_date, end_date)
    ax.set_xticks(xticks)
    ax.set_xticklabels([date_label(month) for month in months], rotation=30)


    # Show max usage in red
    if max_usage is None:
        max_usage = max(total_usage)*1.1
    ax.axhline(max_usage, color='r', linestyle='--', alpha=0.5)

    # Format y-axis
    if ylabel is not None:
        plt.ylabel(ylabel)
    ax.set_ylim(0, 1.2*max_usage)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: str(int(x/1000)) + 'k'))

    # Hide axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)


    # Add gridlines
    for tick in ax.get_yticks():
        plt.axhline(tick, linewidth=0.25, color='k', zorder=0)

    # Hide ticks and remove bottom ytick corresponding to 0 hours
    ax.tick_params(axis='both', length=0)
    ax.set_yticks(ax.get_yticks()[1:])

    if alloc is not None:
        plt.legend([l[0] for l in legend_items], [l[1] for l in legend_items])

    plt.savefig(directory + title + '.' + output_extension, bbox_inches='tight')
    plt.show()

def plot_usage_by_department(total_usage_by_group, start_date, end_date, title, directory=None, output_extension="png"):
    if directory is None:
        directory = ""
    else:
        if directory[-1] != "/":
            directory += "/"
    usage_by_department = {}

    for gid, time in total_usage_by_group.items():
        department = get_department(gid)
        if department not in usage_by_department:
            usage_by_department[department] = 0.
        usage_by_department[department] += time
    fig, ax = plt.subplots(figsize=(16,12))

    departments, time = zip(*[(k, v) for k,v in usage_by_department.items()])
    sorted_inds = np.flip(np.argsort(time))
    departments, time = np.array(departments)[sorted_inds], np.array(time)[sorted_inds]

    ax.barh(departments, time, color='orange')
    plt.yticks(rotation=0)
    plt.xlabel('CPU hours used')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: str(int(x/1000)) + 'k'))

    plt.title(f'{date_label(start_date)} - {date_label(end_date)}', y=1.0, pad=30)
    if title is not None:
        plt.suptitle(title)

    # Hide axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)


    # Add gridlines
    for tick in ax.get_xticks():
        plt.axvline(tick, linewidth=0.25, color='k', zorder=0)

    # Hide ticks and remove bottom ytick corresponding to 0 hours
    ax.tick_params(axis='both', length=0)

    plt.savefig(directory + title + '.' + output_extension, bbox_inches='tight')
    plt.show()

def plot_storage_by_department(storage_by_group, title=None, directory=None, output_extension="png"):
    if directory is None:
        directory = ""
    else:
        if directory[-1] != "/":
            directory += "/"
    storage_by_department = {}

    for gid, storage_usage in storage_by_group.items():
        try:
            department = get_department(gid)
        except ValueError:
            continue
        
        if department not in storage_by_department:
            storage_by_department[department] = 0.

        storage_by_department[department] += storage_usage
    fig, ax = plt.subplots(figsize=(16,12))

    departments, storage_usage = zip(*[(k, v) for k,v in storage_by_department.items()])
    sorted_inds = np.flip(np.argsort(storage_usage))
    departments, storage_usage = np.array(departments)[sorted_inds], np.array(storage_usage)[sorted_inds]

    ax.barh(departments, storage_usage, color='orange')
    plt.yticks(rotation=0)
    plt.xlabel('Storage space used (GB)')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: str(int(x/1000)) + 'k'))

    if title is not None:
        plt.suptitle(title)

    # Hide axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)


    # Add gridlines
    for tick in ax.get_xticks():
        plt.axvline(tick, linewidth=0.25, color='k', zorder=0)

    # Hide ticks and remove bottom ytick corresponding to 0 hours
    ax.tick_params(axis='both', length=0)

    plt.savefig(directory + title.replace('/', '') + '.' + output_extension, bbox_inches='tight')
    plt.show()


def plot_storage_by_group(storage_by_group, cutoff=None, title=None, directory=None, output_extension="png"):
    if directory is None:
        directory = ""
    else:
        if directory[-1] != "/":
            directory += "/"
    fig, ax = plt.subplots(figsize=(16,12))

    groups, storage_usage = zip(*[(k, v) for k,v in storage_by_group.items()])
    sorted_inds = np.flip(np.argsort(storage_usage))
    groups, storage_usage = np.array(groups)[sorted_inds], np.array(storage_usage)[sorted_inds]
    groups = np.array([get_label(id) for id in groups])
    storage_used = sum(storage_usage)
    if cutoff is not None:
        groups, storage_usage = groups[:cutoff], storage_usage[:cutoff]
    
    displayed_storage = sum(storage_usage)
    
    if storage_used != displayed_storage:
        groups = np.append(groups, 'Other')
        storage_usage = np.append(storage_usage, storage_used - displayed_storage)

    ax.barh(groups, storage_usage, color='orange')
    plt.yticks(rotation=0)
    plt.xlabel('Storage space used (GB)')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: str(int(x/1000)) + 'k'))
    if title is not None:
        plt.title(title)

    # Hide axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)


    # Add gridlines
    for tick in ax.get_xticks():
        plt.axvline(tick, linewidth=0.25, color='k', zorder=0)

    # Hide ticks and remove bottom ytick corresponding to 0 hours
    ax.tick_params(axis='both', length=0)

    plt.savefig(directory + title.replace('/', '') + '1.' + output_extension, bbox_inches='tight')
    plt.show()

def plot_storage_by_group_piechart(storage_by_group, cutoff=None, total_storage=None, title=None, legend=True, directory=None, output_extension="png"):
    if directory is None:
        directory = ""
    else:
        if directory[-1] != "/":
            directory += "/"

    if legend:
        import matplotlib.gridspec as gridspec
        
        plt.figure(figsize=(18,10))
        gs = gridspec.GridSpec(1, 2, width_ratios=[2.5,1])
        ax = [plt.subplot(gs[0]), plt.subplot(gs[1])]
    else:
        _, ax = plt.subplots(figsize=(18,10))

    groups, storage_usage = zip(*[(k, v) for k,v in storage_by_group.items()])
    sorted_inds = np.flip(np.argsort(storage_usage))
    groups, storage_usage = np.array(groups)[sorted_inds], np.array(storage_usage)[sorted_inds]
    groups = np.array([get_label(id) for id in groups])
    storage_used = sum(storage_usage)
    if cutoff is not None:
        groups, storage_usage = groups[:cutoff], storage_usage[:cutoff]
    
    color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
    colors = [color_cycle[i % len(color_cycle)] for i in range(len(groups))]
    
    displayed_storage = sum(storage_usage)
    
    if storage_used != displayed_storage:
        groups = np.append(groups, 'Other')
        storage_usage = np.append(storage_usage, storage_used - displayed_storage)
        colors.append('0.6')

    if total_storage is None:
        total_storage = storage_used
    
    if total_storage - storage_used > 0:
        groups = np.append(groups, 'Unused')
        storage_usage = np.append(storage_usage, total_storage - storage_used)
        colors.append('0.3')

    if legend:
        patches, _, _ = ax[0].pie(
            storage_usage, 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            pctdistance=1.2,
        )
        ax[1].legend(patches, groups, loc="center")
        ax[1].axis("off")
        ax = ax[0]
    else:
        ax.pie(
            storage_usage, 
            labels=groups, 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
        )
    
    plt.yticks(rotation=0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: str(int(x/1000)) + 'k'))
    if title is not None:
        plt.suptitle(title)

    # Hide axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)


    # Add gridlines
    for tick in ax.get_xticks():
        plt.axvline(tick, linewidth=0.25, color='k', zorder=0)

    # Hide ticks and remove bottom ytick corresponding to 0 hours
    ax.tick_params(axis='both', length=0)

    plt.subplots_adjust(bottom=0., top=1.0)
    plt.savefig(directory + title.replace('/', '') + '2.' + output_extension, bbox_inches='tight')
    plt.show()
    
# -- Generates excel spreadsheet with all usage information -- #

import openpyxl
from openpyxl.utils import get_column_letter

def monthyear(date):
    month = MONTHS[int(date[5:7])]
    year = date[:4]

    return month, year

def make_report_sheet(report, directory=None):
    if directory is None:
        directory = ""
    else:
        if directory[-1] != "/":
            directory += "/"
    months = report.months
    num_months = len(months)
    groups = GROUPS

    group_usage = report.get_group_usage()

    data_storage = report.query('dataStorage', idx=-1)
    scratch_storage = report.query('scratchStorage', idx=-1)

    report_month, report_year = monthyear(months[-1])

    wb_name = directory + f'ClusterUsage{report_month}{report_year}.xlsx'

    wb = openpyxl.Workbook()

    font = openpyxl.styles.Font(name='Times New Roman')
    fontb = openpyxl.styles.Font(name='Times New Roman', bold=True)


    def make_sheet(sheet, usage_by_group):
        def add_cell(row, col, val, font=font):
            cell = sheet.cell(row=row, column=col)
            cell.value = val
            cell.font = font

        add_cell(4, 1, "Group", fontb)
        sheet.column_dimensions[get_column_letter(1)].width = 20
        add_cell(4, 2, "Department", fontb)
        sheet.column_dimensions[get_column_letter(2)].width = 20

        visited_years = set()

        for n,month in enumerate(months):
            sheet.column_dimensions[get_column_letter(3 + n)].width = 15
            month, year = monthyear(month)
            
            add_cell(5, 3 + n, month, fontb)
            if year not in visited_years:
                visited_years.add(year)
                add_cell(4, 3 + n, year, fontb)

        last_col = 4 + n
        add_cell(5, last_col, "1 Yr Total", fontb)
        sheet.column_dimensions[get_column_letter(last_col)].width = 20
        
        h = 5
        for n,gid in enumerate(groups):
            name = get_user_name(gid)
            department = get_department(gid)
            total_group_usage = sum([usage_by_group[gid][m] for m in range(num_months)])
            if total_group_usage < 1:
                continue

            h += 1
            add_cell(h, 1, name)
            add_cell(h, 2, department)
            for m,_ in enumerate(months):
                if usage_by_group[gid][m] > 1:
                    add_cell(h, 3 + m, round(usage_by_group[gid][m], 1))
            add_cell(h, last_col, round(total_group_usage, 1), fontb)

        last_row = h + 1
        add_cell(last_row, 1, "Total", fontb)

        total_usage = 0
        for i in range(num_months):
            monthly_usage = sum([usage_by_group[gid][i] for gid in groups])
            total_usage += monthly_usage
            add_cell(last_row, 3 + i, round(monthly_usage, 1), fontb)
        add_cell(last_row, last_col, round(total_usage, 1), fontb)

    def make_storage_sheet(sheet, storage):
        def add_cell(row, col, val, font=font):
            cell = sheet.cell(row=row, column=col)
            cell.value = val
            cell.font = font

        add_cell(4, 1, "Group", fontb)
        add_cell(4, 2, "Department", fontb)
        for n,label in enumerate(storage, 3):
            add_cell(4, n, label, fontb)
        
        last_col = 3 + len(storage)
        add_cell(4, last_col, "Total", fontb)

        for i in range(1, 3 + len(storage)):
            sheet.column_dimensions[get_column_letter(i)].width = 30

        h = 5
        for gid in groups:
            if not any([gid in storage[label] and storage[label][gid] > 1 for label in storage]):
                continue

            name = get_user_name(gid)
            department = get_department(gid)
            
            add_cell(h, 1, name)
            add_cell(h, 2, department)
            
            for n,label in enumerate(storage, 3):
                if gid in storage[label] and storage[label][gid] > 1:
                    add_cell(h, n, round(storage[label][gid]), 1)
                
            total_storage = sum([0 if gid not in storage[label] else storage[label][gid] for label in storage])
            add_cell(h, last_col, round(total_storage, 1), fontb)

            h += 1

    sheet = wb.active
    sheet.title = "CPU Usage"
    make_sheet(sheet, group_usage['cpuUsage'])

    sheet = wb.create_sheet("GPU Usage")
    make_sheet(sheet, group_usage['gpuUsage'])

    sheet = wb.create_sheet("Requested MEM")
    make_sheet(sheet, group_usage['reqMem'])

    sheet = wb.create_sheet("Allocated MEM")
    make_sheet(sheet, group_usage['allocMem'])

    sheet = wb.create_sheet("Storage")
    total_group_storage = {
        '/data/ storage (GB)': data_storage, 
        '/scratch/ storage (GB)': scratch_storage,
    }

    make_storage_sheet(sheet, total_group_storage)

    print(f'Saving {wb_name}')
    wb.save(filename=wb_name)



def make_isilon_sheet(report, directory=None):
    if directory is None:
        directory = ""
    else:
        if directory[-1] != "/":
            directory += "/"
    isilon_andromeda_storage = report.query('isilonAndromedaStorage', idx=-1)
    isilon_sirius_storage = report.query('isilonSiriusStorage', idx=-1)
    isilon_full_storage = report.query('isilonStorage', idx=-1)

    # Write all storage usage
    wb = openpyxl.Workbook()
    sheet = wb.active

    font = openpyxl.styles.Font(name='Times New Roman')
    fontb = openpyxl.styles.Font(name='Times New Roman', bold=True)

    def add_cell(row, col, val, font=font):
        cell = sheet.cell(row=row, column=col)
        cell.value = val
        cell.font = font

    ids = list(set(list(isilon_andromeda_storage.keys()) + list(isilon_sirius_storage.keys()) + list(isilon_full_storage.keys())))
    def key(id):
        s = 0
        if id in isilon_andromeda_storage:
            s += isilon_andromeda_storage[id]
        if id in isilon_sirius_storage:
            s += isilon_sirius_storage[id]
        if id in isilon_full_storage:
            s += isilon_full_storage[id]
        return -s

    ids = sorted(ids, key=key)

    add_cell(5, 1, "ID", fontb)
    add_cell(4, 2, "/andromeda_archive/ (GB)", fontb)
    add_cell(4, 3, "/sirius_archive/ (GB)", fontb)
    add_cell(4, 4, "Total Isilon storage (GB)", fontb)

    sheet.column_dimensions[get_column_letter(1)].width = 15
    sheet.column_dimensions[get_column_letter(2)].width = 30
    sheet.column_dimensions[get_column_letter(3)].width = 30
    sheet.column_dimensions[get_column_letter(4)].width = 30
    
    n = 0
    for id in ids:
        in_isilon_andromeda = id in isilon_andromeda_storage and isilon_andromeda_storage[id] > 1
        in_isilon_sirius = id in isilon_sirius_storage and isilon_sirius_storage[id] > 1
        if not in_isilon_andromeda and not in_isilon_sirius:
            continue

        add_cell(5 + n, 1, id, fontb)
        if id in isilon_andromeda_storage:
            if isilon_andromeda_storage[id] > 1:
                add_cell(5 + n, 2, isilon_andromeda_storage[id])
        if id in isilon_sirius_storage:
            if isilon_sirius_storage[id] > 1:
                add_cell(5 + n, 3, isilon_sirius_storage[id])
        if id in isilon_full_storage:
            if isilon_full_storage[id] > 1:
                add_cell(5 + n, 4, isilon_full_storage[id])
        
        n += 1


    wb.save(filename='IsilonStorage.xlsx')