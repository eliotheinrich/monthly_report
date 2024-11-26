This project is used to generate the monthly usage reports for Andromeda. 
When it is first run, it will generate several .pkl files which store historical data on usage and groups.

Usage:

```
git clone https://github.com/eliotheinrich/monthly_report.git
cd monthly_report

module load miniconda3/miniconda
conda create -n monthly_report python=3.10
conda activate monthly_report
pip install requirements.txt

python make_monthly_report.py 2024-11-01 --num-months 13 --directory "October_Report" --output-extension png
```

Additional tags can be provided:

```
-v : verbose output
-i : do not append new data to the historical data files
```
