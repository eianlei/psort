#!/usr/bin/python
# -*- coding: cp1252 -*-
# psort.py 

import argparse
import os
from datetime import datetime

filecount = 0
class File2move(object):
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name
        
        
class Psort_context(object):
    """holds global execution context

    """    
    def __init__(self) -> None:   
        self.import_dir = ""
        self.file_list = []     
        self.jpg_list = []
        self.video_list = []
        self.import_total = 0
        self.skipped_total = 0
        self.bin_days = {}
        self.bin_months = {}    
        self.bin_years = {}
        #newdir_list = []
        #move_list = []

class ImportFile(object):
    def __init__(self, dirpath, filename, ext, number, basename):
        self.dirpath = dirpath
        self.filename = filename
        self.fullpath = os.path.join(dirpath, filename)
        self.mtime = os.path.getmtime(self.fullpath)
        self.ctime = os.path.getctime(self.fullpath)
        self.mtime_dt = datetime.fromtimestamp(self.mtime)
        self.mtime_str = self.mtime_dt.strftime('%Y-%m-%d')
        self.mtime_year = self.mtime_dt.strftime('%Y')
        self.mtime_month = self.mtime_dt.strftime('%Y-%m')
        self.size = os.path.getsize(self.fullpath)        
        self.basename = basename
        self.ext = ext
        self.number = number
        self.dest_path =  ""
        self.new_basename_dest = ""


##################################################################################################### 
def walk_dirs(c):
    new_filecount = 0
    skipped_files = 0

    for dirpath, dirnames, filenames in os.walk(c.import_dir):

        for filename in filenames:
            basename, ext = os.path.splitext(filename)
            fullpath = os.path.join(dirpath, filename)

            ext = ext.upper()
            if ext in [".JPG", ".MP4" ]:
                new_filecount += 1
                new_file = ImportFile(dirpath, filename, ext, new_filecount, basename)

                c.file_list.append(new_file)
                match ext:
                    case '.JPG': 
                        c.jpg_list.append(new_file)
                    case '.MP4': 
                        c.video_list.append(new_file)
            else:    
                # not interested other files
                skipped_files += 1
                continue
    c.import_total += new_filecount
    c.skipped_total += skipped_files

def report_files(c):
    print("JPG files")
    for file in c.jpg_list:
        print(f'{file.number:>6} {file.filename:>16} {file.mtime_str} {file.size}') 
    print("Video files")
    for file in c.video_list:
        print(f'{file.number:>6} {file.filename:>16} {file.mtime_str} {file.size}')         
    return


def group2dmy(c):
    day_keys = []
    bin_days = {}
    month_keys = []
    bin_months = {}
    year_keys = []
    bin_years = {}
    c.file_list.sort(key=lambda x: x.mtime)
    # iterate all files and bin them by mtime
    for file in c.jpg_list:
        # bin by days
        m_day = file.mtime_str
        if m_day in day_keys:
            bin_days[m_day].append(file)
        else:       
            day_keys.append(m_day)
            bin_days[m_day] = [file]
        # bin by months    
        if file.mtime_month in month_keys:
            bin_months[file.mtime_month].append(file)
        else:       
            month_keys.append(file.mtime_month)
            bin_months[file.mtime_month] = [file]            
        # bin by years    
        if file.mtime_year in year_keys:
            bin_years[file.mtime_year].append(file)
        else:       
            year_keys.append(file.mtime_year)
            bin_years[file.mtime_year] = [file]       
    c.bin_days = bin_days
    c.bin_months = bin_months
    c.bin_years = bin_years
    return        
                   
def print_sorted_days(c):
    for i, udate in enumerate(c.bin_days.keys()):
        print(f'== {i+1} {udate} { len(c.bin_days[udate]) }') 
        for file in c.bin_days[udate]:
            print(f'{file.number:>6} {file.filename:>16} {file.mtime_str} {file.size}')  
    
def print_summary(c):
    print(f'*** Yearly bins: {len(c.bin_years)}')
    for i, udate in enumerate(c.bin_years.keys()):
        print(f' Y-BIN #{i+1} year: {udate} files: { len(c.bin_years[udate]) }')  

    print(f'*** Monthly bins: {len(c.bin_months)}')
    for i, udate in enumerate(c.bin_months.keys()):
        print(f' M-BIN #{i+1} month: {udate} files: { len(c.bin_months[udate]) }')  
            
    print(f'*** daily bins {len(c.bin_days)}')
    for i, udate in enumerate(c.bin_days.keys()):
        print(f' D-BIN #{i+1} date: {udate} files: { len(c.bin_days[udate]) }')  
    return

def extract_special(c):
    print(f'SPECIAL: from {c.import_dir} extract date {c.special_date}')
    print(f' to {c.output_dir}\\{c.special_dir}')
    if c.special_date not in c.bin_days.keys():
        print(f'date {c.special_date} not found, abort operation')
    return
        
###############################################################################
# Python script MAIN
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="import jpg and video files, sort and move to destinations")
    parser.add_argument('-i','--input', help='input directory to be sorted')
    parser.add_argument('-o','--output', help='output directory')
    parser.add_argument('-t','--trip', help='do trip sorting, give trip label')
    parser.add_argument('-n','--name', help='for trip sorting daily prefix label')
    parser.add_argument('-s','--special', help='special date extraction, give date in b arg')    
    parser.add_argument('-b','--begin', help='begin date of the trip or special event date, format YYYY-MM-DD')
    parser.add_argument('-e','--end', help='end date of the trip, format YYYY-MM-DD')
    #
    parser.add_argument('-r','--report',help='report only',action='store_true')
    parser.add_argument('-z','--zort',help='report files sorted by dates',action='store_true')
    parser.add_argument('--summary',help='summary of years, months, days',action='store_true')

    args = parser.parse_args()
    #de = dotenv.load_dotenv(verbose=True)
    
    c = Psort_context()
    c.import_dir = args.input
    c.output_dir = args.output
    c.special_dir = args.special
    c.special_date = args.begin
    
    walk_dirs(c)
    group2dmy(c)

    if args.report:
        report_files(c)
    elif args.zort:
        print_sorted_days(c)
    elif args.summary:
        print_summary(c)
    elif args.special:
        extract_special(c)
        pass
