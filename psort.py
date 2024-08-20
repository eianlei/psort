#!/usr/bin/python
# -*- coding: cp1252 -*-
# psort.py 

import argparse
import os, shutil
from pathlib import Path
from datetime import datetime, date, timedelta

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
    in_path = Path(c.import_dir)
    if in_path.is_dir():
        print(f'scanning {c.import_dir}')
    else:
        print(f'ABORT! does not exist: {c.import_dir}')
        quit()
        
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
    out_dir = f'{c.output_dir}\\{c.special_dir}'
    print(f'SPECIAL: from {c.import_dir} extract date {c.special_date}')
    print(f' to {out_dir}')
    if c.special_date not in c.bin_days.keys():
        print(f'date {c.special_date} not found, abort operation')
    
    if c.mode_bat: 
        batfile_name = f'move_{c.special_date}.bat'
        batfile = open(batfile_name, mode="w")
        batfile.write(f'REM this moves JPG files from {c.import_dir} to {out_dir}\n')
        batfile.write('CHCP 1252\n')
        batfile.write(f'MKDIR "{out_dir}"\n')
        for file in c.bin_days[c.special_date]:
            new_name = f'{out_dir}{os.sep}{file.filename}'
            batfile.write(f'MOVE "{file.fullpath}" "{new_name}"\n')
        batfile.close()     
        print(f'created {batfile_name}') 
    elif c.mode_dryrun:
        print("# DRY RUN")
        print(f'MKDIR "{out_dir}"')
        for file in c.bin_days[c.special_date]:
            new_name = f'{out_dir}{os.sep}{file.filename}'
            print(f'MOVE "{file.fullpath}" "{new_name}"')
    else:
        dest_path = Path(out_dir)
        if dest_path.is_dir():
            print(f'directory {out_dir} exists already\n')
        else:
            print(f'creating {out_dir} \n')
            Path.mkdir(dest_path)    
        fnum = 0
        for file in c.bin_days[c.special_date]:
            #new_name = f'{out_dir}{os.sep}{file.filename}'
            shutil.move(file.fullpath, dest_path)
            fnum += 1
        print(f'moved {fnum} files')                
    return


def extract_trip(c):
    trip_dates = []
    out_dir = f'{c.output_dir}{os.sep}{c.trip}'
    day_out_dirs = {}
    print(f'TRIP: from {c.import_dir} begin: {c.trip_begin} end: {c.trip_end}')
    print(f' to {out_dir}, date prefix {c.trip_name} ')
    # begin_date = date(year=int(c.trip_begin[0:4]), month=int(c.trip_begin[5:7]),day=int(c.trip_begin[8:10])) 
    # end_date =   date(year=int(c.trip_end[0:4]),   month=int(c.trip_end[5:7]),  day=int(c.trip_end[8:10])) 
    begin_date = datetime.strptime(c.trip_begin, "%Y-%m-%d")
    end_date = datetime.strptime(c.trip_end, "%Y-%m-%d")
    d = begin_date
    delta = timedelta(days=1)
    while d <= end_date:
        ds = d.strftime('%Y-%m-%d')
        if ds in c.bin_days.keys():
            trip_dates.append(ds)
            day_out_dir = f'{out_dir}{os.sep}{c.trip_name} {ds}'
            day_out_dirs[ds] = day_out_dir
            print(f'sub-dir "{c.trip_name} {ds}" {len(c.bin_days[ds])} files')
        d += delta
    

    if c.mode_dryrun:
        print("# DRY RUN")
        print(f'MKDIR "{out_dir}"')
        for date in trip_dates:
            day_out_dir = day_out_dirs[date]
            print(f'MKDIR "{day_out_dir}"')
            for file in c.bin_days[date]:
                new_name = f'{day_out_dir}{os.sep}{file.filename}'
                print(f'MOVE "{file.fullpath}" "{new_name}"')
        return
    elif c.mode_bat: 
        batfile_name = f'move_{c.trip}.bat'
        batfile = open(batfile_name, mode="w")
        batfile.write(f'REM this moves JPG files from {c.import_dir} to {out_dir}\n')
        batfile.write('CHCP 1252\n')
        batfile.write(f'MKDIR "{out_dir}"\n')
        for date in trip_dates:
            day_out_dir = day_out_dirs[date]
            batfile.write(f'MKDIR "{day_out_dir}"\n')
            for file in c.bin_days[date]:
                new_name = f'{day_out_dir}{os.sep}{file.filename}'
                batfile.write(f'MOVE "{file.fullpath}" "{new_name}"\n') 
        batfile.close()     
        print(f'created {batfile_name}') 
        return
    else:
        dest_path = Path(out_dir)
        if dest_path.is_dir():
            print(f'directory {out_dir} exists already')
        else:
            print(f'creating {out_dir} \n')
            Path.mkdir(dest_path)    
        fnum = 0
        dnum = 0
        for date in trip_dates:
            day_out_dir = day_out_dirs[date]
            day_dest_path = Path(day_out_dir)
            if day_dest_path.is_dir():
                print(f'directory {day_out_dir} exists already')
            else:
                print(f'creating {day_out_dir} ')
                Path.mkdir(day_dest_path)        

            for file in c.bin_days[date]:
                shutil.move(file.fullpath, day_dest_path)
                fnum += 1
            dnum += 1
        print(f'moved {fnum} files for {dnum} days')                
    return
        
###############################################################################
# Python script MAIN
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="import jpg and video files, sort and move to destinations")
    parser.add_argument('-i','--input', help='input directory to be sorted',required=True)
    parser.add_argument('-o','--output', help='output directory') #,required=True)
    parser.add_argument('-t','--trip', help='do trip sorting, give trip label')
    parser.add_argument('-n','--name', help='for trip sorting daily prefix label')
    parser.add_argument('-s','--special', help='special date extraction, give date in b arg')    
    parser.add_argument('-b','--begin', help='begin date of the trip or special event date, format YYYY-MM-DD')
    parser.add_argument('--batfile', help='create BAT file', action='store_true')
    parser.add_argument('-e','--end', help='end date of the trip, format YYYY-MM-DD')
    parser.add_argument('-d','--dryrun', help='dry run, nothing touched', action='store_true')
    #
    parser.add_argument('-r','--report',help='report only',action='store_true')
    parser.add_argument('-z','--zort',help='report files sorted by dates',action='store_true')
    parser.add_argument('--summary',help='summary of years, months, days',action='store_true')

    args = parser.parse_args()
    #de = dotenv.load_dotenv(verbose=True)
    
    c = Psort_context()
    c.import_dir = args.input
    c.output_dir = args.output
    c.trip_dir = args.trip
    c.special_dir = args.special
    c.special_date = args.begin
    c.mode_bat = args.batfile
    c.mode_dryrun = args.dryrun
    
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
    elif args.trip:
        c.trip = args.trip
        c.trip_begin = args.begin
        c.trip_end = args.end
        c.trip_name = args.name
        extract_trip(c)    
    else:
        print('no commands given')
        quit()
