#!/usr/bin/python
# -*- coding: cp1252 -*-
# psort.py 

import argparse
import atexit
from enum import Enum
from io import TextIOWrapper
import os, shutil, sys
from pathlib import Path
from datetime import datetime, date, timedelta
from progress.bar import Bar
from exif import Image 

class OPMODE(Enum):
    DRYRUN = 1
    MOVE = 2
    COPY = 3
    BATCOPY = 4
    BATMOVE = 5

class File2move(object):
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name
        
        
class Psort_context(object):
    """holds global execution context

    """    
    def __init__(self) -> None:   
        self.args = ""
        self.date: datetime
        self.opmode = OPMODE.DRYRUN
        self.import_dir = ""
        self.importPath: Path
        self.output_dir = ""
        self.trip_dir = ""
        self.trip_begin = ""
        self.trip_end = ""
        self.trip_name = ""
        self.special_dir = ""
        self.special_date = ""
        self.mode_bat = False
        self.mode_dryrun = False
        self.dryrun_file = "dryrun.txt"
        self.logfile_name = "log.txt"
        self.logfile_fd : TextIOWrapper
        self.batfile_name = "PSORT.BAT"
        self.batfile_fd : TextIOWrapper
        self.mode_exif = False
        self.mode_move = False
        self.file_list = []     
        self.jpg_list = []
        self.video_list = []
        self.import_total = 0
        self.skipped_total = 0
        self.subdirs = 0
        self.bin_days = {}
        self.bin_months = {}    
        self.bin_years = {}
        self.ok_transfers = 0
        self.skip_transfers = 0
        self.rename_transfers = 0
        self.newdirs_done = 0
        self.newdirs_skip = 0
        self.mode_nodup = False
        #newdir_list = []
        #move_list = []

class ImportFile(object):
    def __init__(self, dirpath, filename, ext, number, basename):
        self.dirpath = dirpath
        self.filename = filename
        self.fullpath = os.path.join(dirpath, filename)
        self.mtime = os.path.getmtime(self.fullpath)
        self.ctime = os.path.getctime(self.fullpath)
        self.otime = self.mtime if self.mtime <= self.ctime else self.ctime
        self.otime_dt = datetime.fromtimestamp(self.otime)
        self.otime_str = self.otime_dt.strftime('%Y-%m-%d')
        self.otime_year = self.otime_dt.strftime('%Y')
        self.otime_month = self.otime_dt.strftime('%Y-%m')
        self.exif = False
        self.d_exif = ""
        self.size = os.path.getsize(self.fullpath)        
        self.basename = basename
        self.ext = ext
        self.number = number
        self.dest_path =  ""
        self.new_basename_dest = ""


##################################################################################################### 
def walk_dirs(c: Psort_context):
    in_path = Path(c.import_dir)
    if in_path.is_dir():
        print(f'scanning {c.import_dir}')
    else:
        print(f'ABORT! does not exist: {c.import_dir}')
        quit()
        
    new_filecount = 0
    skipped_files = 0
    n = 0
    for dirpath, dirnames, filenames in os.walk(c.import_dir):
        sys.stdout.write(f'{n}\r')
        sys.stdout.flush()
        n += 1

        for filename in filenames:
            basename, ext = os.path.splitext(filename)
            #fullpath = os.path.join(dirpath, filename)

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
            sys.stdout.write(f'{new_filecount} {skipped_files}\r')
            sys.stdout.flush()
    c.import_total += new_filecount
    c.skipped_total += skipped_files
    
def analyze_file(c: Psort_context, full_path: str):
    if isinstance(full_path, Path):
        filename = full_path.name     
    else:    
        filename = os.path.basename(full_path)
    basename, ext = os.path.splitext(filename)
    dirpath = os.path.dirname(full_path)
    #full_path = os.path.join(dirpath, filename)

    ext = ext.upper()
    if ext in [".JPG", ".MP4" ]:
        c.import_total += 1
        new_file = ImportFile(dirpath, filename, ext, c.import_total, basename)
        c.file_list.append(new_file)
        match ext:
            case '.JPG': 
                c.jpg_list.append(new_file)
            case '.MP4': 
                c.video_list.append(new_file)
    else:    
        # not interested other files
        c.skipped_total += 1
        
    sys.stdout.write(f'{c.import_total} {c.skipped_total}\r')
    sys.stdout.flush()    
    return


def scan_files_rec2(c: Psort_context, path: str):
    obj = os.scandir(path)
    for entry in obj:
        if entry.is_dir():
            scan_files_rec2(c, entry)
            c.subdirs +=1
        elif entry.is_file():
                        # get datetime of the file mtime
            fdt = datetime.fromtimestamp( os.stat(entry).st_mtime)
            if fdt > c.date:
                analyze_file(c, entry)     
            else:
                c.skipped_total += 1
                sys.stdout.write(f'{c.import_total} {c.skipped_total}\r')
                sys.stdout.flush()    
    obj.close()
    return
    
def scan_files_recursive(c: Psort_context, path: str):
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            c.subdirs +=1
            scan_files_recursive(c, full_path)
        else:
            analyze_file(c, full_path)     
    return

def scan_files_iterdir(c: Psort_context, path):
    # print(f'iter {path.name}')
    obj = path.iterdir()
    for entry in obj:
        if entry.is_dir():
            c.subdirs +=1
            scan_files_iterdir(c, entry)
        elif entry.is_file():
            # get datetime of the file mtime
            fdt = datetime.fromtimestamp( os.stat(entry).st_mtime)
            if fdt > c.date:
                analyze_file(c, entry)     
            else:
                c.skipped_total += 1
    return

def check_import_dir(c: Psort_context):
    c.importPath = Path(c.import_dir)
    if c.importPath.is_dir():
        print(f'scanning {c.import_dir}')
    else:
        print(f'ABORT! does not exist: {c.import_dir}')
        quit()

def report_files(c: Psort_context):
    print("JPG files")
    for file in c.jpg_list:
        print(f'{file.number:>6} {file.filename:>16} {file.otime_str} {file.size} {file.d_exif}') 
    print("Video files")
    for file in c.video_list:
        print(f'{file.number:>6} {file.filename:>16} {file.otime_str} {file.size}')         
    return

def special_day(c: Psort_context):
    c.bin_days = {}
    c.bin_days[c.special_date] = []
    for file in c.jpg_list:
        if file.otime_str == c.special_date:
            c.bin_days[c.special_date].append(file) 
    if len(c.bin_days[c.special_date]) == 0:
        print(f'{c.special_date} no files!!')
        quit()
    return        

def group2dmy(c: Psort_context):
    day_keys = []
    bin_days = {}
    month_keys = []
    bin_months = {}
    year_keys = []
    bin_years = {}
    bar = Bar('group jpg files ', max=len(c.jpg_list))
    c.file_list.sort(key=lambda x: x.otime)
    # iterate all files and bin them by otime
    for file in c.jpg_list:
        # bin by days
        m_day = file.otime_str
        if c.mode_exif:
            with open(file.fullpath, 'rb') as jpg_file:
                jpg_bytes = jpg_file.read()
            jpg_image = Image(jpg_bytes)    
            if jpg_image.has_exif:
                file.exif = True
                file.d_exif = jpg_image.datetime_original
                m_day = f'{file.d_exif[0:4]}-{file.d_exif[5:7]}-{file.d_exif[8:10]}'
        
        if m_day in day_keys:
            bin_days[m_day].append(file)
        else:       
            day_keys.append(m_day)
            bin_days[m_day] = [file]
        # bin by months    
        if file.otime_month in month_keys:
            bin_months[file.otime_month].append(file)
        else:       
            month_keys.append(file.otime_month)
            bin_months[file.otime_month] = [file]            
        # bin by years    
        if file.otime_year in year_keys:
            bin_years[file.otime_year].append(file)
        else:       
            year_keys.append(file.otime_year)
            bin_years[file.otime_year] = [file]      
        bar.next()
    bar.finish()     
    c.bin_days = bin_days
    c.bin_months = bin_months
    c.bin_years = bin_years
    return        
                   
def print_sorted_days(c: Psort_context):
    for i, udate in enumerate(c.bin_days.keys()):
        print(f'== {i+1} {udate} { len(c.bin_days[udate]) }') 
        for file in c.bin_days[udate]:
            print(f'{file.number:>6} {file.filename:>16} {file.otime_str} {file.size}')  
    
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

def extract_special(c: Psort_context):
    out_dir = f'{c.output_dir}\\{c.special_dir}'
    if c.special_date not in c.bin_days.keys():
        error_txt = f'date {c.special_date} not found, abort operation'
        print(error_txt)
        print2log(c.logfile_fd, error_txt)
        return
    
    begin_txt = f'SPECIAL: from {c.import_dir} extract date {c.special_date} to {out_dir}'
    print(begin_txt)
    print2log(c.logfile_fd, begin_txt)
    
    dir_create(out_dir, c)
    fnum = 0
    bar = Bar(f'transfer {c.special_date}', max=len(c.bin_days[c.special_date]))
    for file in c.bin_days[c.special_date]:
        new_name = f'{out_dir}{os.sep}{file.filename}'
        copymove(file.fullpath, new_name, c)
        fnum += 1
        bar.next()
    bar.finish()    
    end_txt = f'transerred {fnum} files'
    print(end_txt)
    print2log(c.logfile_fd, end_txt)
    return


def extract_trip(c: Psort_context):
    """_summary_ implements --trip

    Args:
        c (Psort_context): 
        c.trip_dir trip subdirectory name
    """
    trip_dates = []
    out_dir = f'{c.output_dir}{os.sep}{c.trip_dir}'
    day_out_dirs = {}
    
    begin_txt = f'TRIP: from {c.import_dir} begin: {c.trip_begin} end: {c.trip_end} to {out_dir}, date prefix {c.trip_name}'
    print(begin_txt)
    print2log(c.logfile_fd, begin_txt)
    
    begin_date = datetime.strptime(c.trip_begin, "%Y-%m-%d")
    end_date   = datetime.strptime(c.trip_end, "%Y-%m-%d")
    one_day    = timedelta(days=1)
    
    # create trip_dates[] list
    this_date = begin_date
    while this_date <= end_date:
        ds = this_date.strftime('%Y-%m-%d')
        if ds in c.bin_days.keys():
            trip_dates.append(ds)
            day_out_dir = f'{out_dir}{os.sep}{c.trip_name} {ds}'
            day_out_dirs[ds] = day_out_dir
            print(f'sub-dir "{c.trip_name} {ds}" {len(c.bin_days[ds])} files')
        this_date += one_day
    
    # main functionality
    dir_create(out_dir, c)
    fnum = 0
    dnum = 0
    for date in trip_dates:
        day_out_dir = day_out_dirs[date]
        dir_create(day_out_dir, c)

        bar = Bar(f'transfer {date}', max=len(c.bin_days[date]))
        for file in c.bin_days[date]:
            new_name = f'{day_out_dir}{os.sep}{file.filename}'
            copymove(file.fullpath, new_name, c)
            fnum += 1
            bar.next()
        bar.finish()    
        dnum += 1
    end_txt = f'transferred {fnum} files for {dnum} days'
    print(end_txt) 
    print2log(c.logfile_fd, end_txt)   
    return

def dir_create(dir: str, c: Psort_context):
    dest_path = Path(dir)
    if dest_path.is_dir():
        print2log(c.logfile_fd, f'directory {dir} exists already')
        c.newdirs_skip += 1
        return
    match c.opmode:
        case OPMODE.DRYRUN:
            print2log(c.logfile_fd, f'dryrun: would create {dir}\n')
            return
        case OPMODE.MOVE | OPMODE.COPY:
            print2log(c.logfile_fd, f' creating {dir}')
            Path.mkdir(dest_path)    
            return
        case OPMODE.BATMOVE | OPMODE.BATCOPY:
            print2log(c.logfile_fd, f'BAT creating {dir}')
            c.batfile_fd.write(f'MKDIR "{dir}"\n')
    return

def copymove(source: str, destination: str, c: Psort_context):
    dest_path = Path(destination)
    if dest_path.is_file():
        if c.mode_nodup:
            root, ext = os.path.splitext(destination)
            destination = f'{root}(1){ext}'
            print2log(c.logfile_fd, f'file exists, rename copy {destination}')
            c.rename_transfers += 1
        else:
            if c.mode_move:
                print2log(c.logfile_fd, f'DELETE/MOVE again: "{source}" already at "{destination}"')
            else:
                print2log(c.logfile_fd, f'SKIP: "{source}" already at "{destination}"')
                c.skip_transfers += 1
                return

    match c.opmode:
        case OPMODE.DRYRUN:
            if c.mode_move:
                op = 'DRYmove'
            else:    
                op = 'DRYcopy'
        case OPMODE.MOVE:
            op = "MOVE"
            shutil.move(source, destination)
        case OPMODE.COPY:
            op = "COPY2"
            shutil.copy2(source, destination)
        case OPMODE.BATCOPY:
            op = "BATCOPY"
            c.batfile_fd.write(f'COPY "{source}" "{destination}"\n')
        case OPMODE.BATMOVE:
            op = "BATMOVE"
            c.batfile_fd.write(f'MOVE "{source}" "{destination}"\n')
    c.ok_transfers += 1
    print2log(c.logfile_fd, f'{op} "{source}" "{destination}"')
    return

def print2log(fd: TextIOWrapper, text: str):
    timestamp = datetime.now().isoformat()
    fd.write(f'{timestamp} {text}\n')
    return

def extract_year(c: Psort_context, year: str):
    print2log(c.logfile_fd, f"extract_year {year}")
    this_year_months = []
    for month in c.bin_months.keys():
        if month[0:4] == year:
            this_year_months.append(month)
            
    out_dir = f'{c.output_dir}{os.sep}{year}'
    dir_create(out_dir, c)
    fnum = 0
    mnum = 0
    for month in this_year_months:
        month_out_dir = f'{out_dir}{os.sep}{month}'
        dir_create(month_out_dir, c)
        op = 'MOVing' if c.mode_move else 'COPYing'
        bar = Bar(f'{op} {month}', max=len(c.bin_months[month]))
        for file in c.bin_months[month]:
            new_name = f'{month_out_dir}{os.sep}{file.filename}'
            # shutil.move(file.fullpath, new_name)
            copymove(file.fullpath, new_name, c)
            fnum += 1
            bar.next()
        bar.finish()    
        mnum += 1
    op = 'MOVEed' if c.mode_move else 'COPied'
    end_txt = f'year {year}: {op} {fnum} files for {mnum} months'
    print(end_txt) 
    print2log(c.logfile_fd, end_txt)
    return

def version_print():
    version = 0.9
    release_date = "2025-08-04"
    print(f'psort.py version {version} released {release_date}')
    print('CC BY-NC-SA 4.0 Copyright (c) 2025 Ian Leiman')
    print('https://creativecommons.org/licenses/by-nc-sa/4.0/')
    print('https://github.com/eianlei/psort')

def create_logfile(c: Psort_context):
    logtime = datetime.now().strftime('%Y%m%d_%H%M%S')
    c.logfile_name = f'{logtime}_LOG.TXT'
    c.logfile_fd = open(c.logfile_name, 'w')
    atexit.register(c.logfile_fd.close)
    print2log(c.logfile_fd, f'logfile start')
    c.logfile_fd.write(f'{c.args}/n') 
    return

def create_batfile(c: Psort_context):
    c.batfile_fd = open(c.batfile_name, 'w')
    print2log(c.logfile_fd, f'create batfile {c.batfile_name}')
    c.batfile_fd.write(f'REM this extracts files from {c.import_dir}\n')
    c.batfile_fd.write('CHCP 1252\n')
    atexit.register(c.batfile_fd.close)
    return
        
###############################################################################
# Python script MAIN
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="import jpg and video files, sort and move to destinations")
    group1 = parser.add_mutually_exclusive_group(required=True)
    group1.add_argument('-i','--input', help='input directory to be sorted')
    group1.add_argument('-v','--version', help='version information', action='store_true') 
    #
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-y', '--year', help='year to extract')
    group2.add_argument('-s', '--special', help='special date extraction, give date in b arg')       
    group2.add_argument('-t', '--trip', help='do trip sorting, give trip label')    
    group2.add_argument('-r', '--report',help='report only',action='store_true')
    group2.add_argument('-z', '--zort',help='report files sorted by dates',action='store_true')
    group2.add_argument('-S', '--summary',help='summary of years, months, days',action='store_true')
    #
    parser.add_argument('-o','--output', help='output directory') #,required=True)
    parser.add_argument('-n','--name', help='for trip sorting daily prefix label')
    parser.add_argument('-b','--begin', help='begin date of the trip or special event date, format YYYY-MM-DD')
    parser.add_argument('-B','--batfile', help='create BAT file')
    parser.add_argument('-e','--end', help='end date of the trip, format YYYY-MM-DD')
    parser.add_argument('-d','--dryrun', help='dry run, nothing touched', action='store_true')
    parser.add_argument('-l','--limit', help='file count limit to create directory for a date')
    parser.add_argument('-D','--date', help= 'start date for copy/move')
    #

    parser.add_argument('--exif', help='use EXIF date instead of file timestamp', action='store_true')
    parser.add_argument('-M', '--move', help='move files instead of copy, copy is default', action='store_true')
    parser.add_argument('-X', '--nodup', help='do not skip duplicates at destination but rename a copy', action='store_true')

    args = parser.parse_args()
    #de = dotenv.load_dotenv(verbose=True)
    
    if args.version:
        version_print()
        quit()
    
    c = Psort_context()
    c.args = ' '.join(sys.argv)
    c.import_dir = args.input
    c.output_dir = args.output
    # c.trip_dir = args.trip

    c.mode_exif = args.exif
    c.mode_nodup = args.nodup
    
    create_logfile(c)
    
    if args.batfile:
        c.mode_bat = True
        c.opmode = OPMODE.BATCOPY
        c.batfile_name = args.batfile
        create_batfile(c)
    elif args.move:
        c.mode_move = True
        c.mode_dryrun = False
        c.opmode = OPMODE.MOVE
    else:
        c.mode_move = False
        c.mode_dryrun = False
        c.opmode = OPMODE.COPY       
    
    if args.date:
        c.date = datetime.strptime(args.date, "%Y-%m-%d")
        print(f'start date {c.date.isoformat()}')
    else:
        c.date = datetime(year=1900,month=1, day=1)
        print('no start date given')
    
    if args.dryrun:
        c.opmode = OPMODE.DRYRUN
        c.mode_dryrun = True
        #c.dryrun_file = "dryrun.txt"
        print(f"*** DRY RUN MODE *** nothing is actually done, after exit read {c.logfile_name} ")
        #c.dryrun_fd = open(c.dryrun_file, 'w')
        #atexit.register(c.dryrun_fd.close)

    check_import_dir(c)
    # walk_dirs(c)
    # scan_files_recursive(c, c.import_dir)
    # scan_files_iterdir(c, c.importPath)
    # only the scan_files_rec2() iterates files one by one 
    scan_files_rec2(c, c.import_dir)
    print(f'{c.import_total} files importing, {c.skipped_total} skipped, {len(c.jpg_list)} JPG, in {c.subdirs} sub directories')
    
    if args.special:
        if args.special != "":
            c.special_dir = args.special
        else:
            print('no directory given as argument to -s')
            quit()
        if args.begin != "":
            c.special_date = args.begin
        else:
            print('no date given as argument to -b')
            quit()           
        special_day(c)
        extract_special(c)
        quit()
    else:
        group2dmy(c)

    if args.report:
        report_files(c)
    elif args.zort:
        print_sorted_days(c)
    elif args.summary:
        print_summary(c)
 
    elif args.trip:
        c.trip_dir = args.trip
        c.trip_begin = args.begin
        c.trip_end = args.end
        c.trip_name = args.name
        extract_trip(c)    
        
    elif args.year:
        extract_year(c, args.year)
        # c.dryrun_fd.close() done by atexit
    else:
        print('no commands given')
        quit()
    quit()    
        
