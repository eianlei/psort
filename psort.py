#!/usr/bin/python
# -*- coding: cp1252 -*-
# psort.py 

import argparse
import os, shutil, sys
from pathlib import Path
from datetime import datetime, date, timedelta
from progress.bar import Bar
from exif import Image 

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
        self.output_dir = ""
        self.trip_dir = ""
        self.trip_begin = ""
        self.trip_end = ""
        self.trip_name = ""
        self.special_dir = ""
        self.special_date = ""
        self.mode_bat = False
        self.mode_dryrun = False
        self.mode_exif = False
        self.mode_move = False
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
def walk_dirs(c):
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

def report_files(c):
    print("JPG files")
    for file in c.jpg_list:
        print(f'{file.number:>6} {file.filename:>16} {file.otime_str} {file.size} {file.d_exif}') 
    print("Video files")
    for file in c.video_list:
        print(f'{file.number:>6} {file.filename:>16} {file.otime_str} {file.size}')         
    return

def special_day(c):
    c.bin_days = {}
    c.bin_days[c.special_date] = []
    for file in c.jpg_list:
        if file.otime_str == c.special_date:
            c.bin_days[c.special_date].append(file) 
    if len(c.bin_days[c.special_date]) == 0:
        print(f'{c.special_date} no files!!')
        quit()
    return        

def group2dmy(c):
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
                   
def print_sorted_days(c):
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
        bar = Bar(f'moving {c.special_date}', max=len(c.bin_days[c.special_date]))
        for file in c.bin_days[c.special_date]:
            #new_name = f'{out_dir}{os.sep}{file.filename}'
            shutil.move(file.fullpath, dest_path)
            fnum += 1
            bar.next()
        bar.finish()    
        print(f'moved {fnum} files')                
    return


def extract_trip(c):
    """_summary_ implements --trip

    Args:
        c (Psort_context): 
        c.trip_dir trip subdirectory name
    """
    trip_dates = []
    out_dir = f'{c.output_dir}{os.sep}{c.trip_dir}'
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
        batfile_name = f'move_{c.trip_dir}.bat'
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

            bar = Bar(f'moving {date}', max=len(c.bin_days[date]))
            for file in c.bin_days[date]:
                shutil.move(file.fullpath, day_dest_path)
                fnum += 1
                bar.next()
            bar.finish()    
            dnum += 1
        print(f'moved {fnum} files for {dnum} days')                
    return

def dir_create(dir, create):
    dest_path = Path(dir)
    if dest_path.is_dir():
        print(f'directory {dir} exists already')
        return
    else:
        if create:
            print(f'really creating {dir}')
            Path.mkdir(dest_path)    
        else:
            print(f'dryrun: would create {dir}')
    return

def copymove(source, destination, dryrun, move):
    dest_path = Path(destination)
    if dest_path.is_file():
        print(f'{destination} exists already')
    if dryrun:
        op = 'MOVE' if move else 'COPY'
        print(f'dryrun: {op} "{source}" "{destination}"')
    else:
        if move:
            shutil.move(source, destination)
        else:
            shutil.copy2(source, destination)
    return
  

def extract_year(c, year):
    out_dir = f'{c.output_dir}{os.sep}{year}'
    this_year_months = []
    for month in c.bin_months.keys():
        if month[0:4] == year:
            this_year_months.append(month)
            
    if c.mode_dryrun:
        print(f"# DRY RUN {year}")
        dir_create(out_dir, False)
      
        for month in this_year_months:
            month_out_dir = f'{out_dir}{os.sep}{month}'
            dir_create(month_out_dir, False)
            for file in c.bin_months[month]:
                new_name = f'{month_out_dir}{os.sep}{file.filename}'
                print(f'MOVE "{file.fullpath}" "{new_name}"')
    else:
        dir_create(out_dir, True)
        fnum = 0
        mnum = 0
        for month in this_year_months:
            month_out_dir = f'{out_dir}{os.sep}{month}'
            dir_create(month_out_dir, True)
            bar = Bar(f'moving {month}', max=len(c.bin_months[month]))
            for file in c.bin_months[month]:
                new_name = f'{month_out_dir}{os.sep}{file.filename}'
                shutil.move(file.fullpath, new_name)
                fnum += 1
                bar.next()
            bar.finish()    
            mnum += 1
        print(f'moved {fnum} files for {mnum} months')          
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
    parser.add_argument('-l','--limit', help='file count limit to create directory for a date')
    parser.add_argument('-y','--year', help='year to extract')
    #
    parser.add_argument('-r','--report',help='report only',action='store_true')
    parser.add_argument('-z','--zort',help='report files sorted by dates',action='store_true')
    parser.add_argument('--summary',help='summary of years, months, days',action='store_true')
    parser.add_argument('--exif', help='use EXIF date instead of file timestamp', action='store_true')
    parser.add_argument('-M', '--move', help='move files instead of copy, copy is default', action='store_true')

    args = parser.parse_args()
    #de = dotenv.load_dotenv(verbose=True)
    
    c = Psort_context()
    c.import_dir = args.input
    c.output_dir = args.output
    # c.trip_dir = args.trip
    c.special_dir = args.special
    c.special_date = args.begin
    c.mode_bat = args.batfile
    c.mode_dryrun = args.dryrun
    c.mode_exif = args.exif
    c.mode_move = args.move
    
    walk_dirs(c)
    if args.special:
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
    else:
        print('no commands given')
        quit()
    quit()    
        
