# psort, is a photo sorting app in python

This command line app is used to sort incoming photo files from camera into a well organized directory structure. Photos can be sorted such that photos taken in each month go into their own directory, such as "../2024/05/", or photos taken on a specific date go to a specially named directory, such as "../2023-12-24 xmas-eve/", or photos taken during a specific range of days go to a special directory sorted by days, such as ".. /2024 Paris-vacation/Paris 2024-06-01/". The app is controlled by command line options and mainly intended to run on Windows, although there is nothing to prevent it running on Linux or Mac. The app can move the files itself, or it can create a Windows BAT-file to execute the moves, or you can do a dry run to verify first what would happen.

# dependencies
- The Python app requires Python 3.10 or greater 
- argparse
- os.walk
- progress.bar
- exif (only needed if you want to use --exif option)
# command line options

| **-** | **--**  | **help text**                                                   |
| ----- | ------- | --------------------------------------------------------------- |
| **i** | input   | input directory to be sorted                                    |
| **D** | date    | start date for copy/move
| **o** | output  | output directory                                                |
| **t** | trip    | do trip sorting, give trip label                                |
| **n** | name    | for trip sorting daily prefix label                             |
| **s** | special | special date extraction, give date in b arg                     |
| **b** | begin   | begin date of the trip or special event date, format YYYY-MM-DD |
| **M** | move    | move files instead of copy, copy is default                     |
|       | batfile | create BAT file, instead of executing moves                     |
| **e** | end     | end date of the trip, format YYYY-MM-DD                         |
| **d** | dryrun  | dry run, nothing touched                                        |
| **y** | year    | year to extract YYYY                                            |
| **r** | report  | report only                                                     |
| **z** | zort    | report files sorted by dates                                    |
|       | summary | summary of years, months, days                                  |
|       | exif    | use EXIF date instead of file timestamp                         |
|       | nodup   | do not skip duplicates at destination but rename a copy         |
|       | mark    | mark copied files to markfile   |

# date format
Using [ISO 8601 date format](https://en.wikipedia.org/wiki/ISO_8601), which is **YYYY-MM-DD**.
For example 21st January 2024 is **2024-01-21**.
January 2024 is **2024-01**

# example command lines
In all these examples the incoming directory is "Z:\\photos\\INCOMING" specified by the -i option.
```
# report all JPG and MP4 files
python psort.py -i "Z:\photos\INCOMING" -r

# report file counts per year, month, date
python psort.py -i "Z:\photos\INCOMING" –summary

# report files grouped by dates of month 2024-01
python psort.py -i "D:\MEDIA\JPG\HOME\2024\2024-01" -z

# import a trip to  "2024-01 Val Thorens" date range from 2024-01-27 to 2024-02-04
python psort.py -i "Z:\photos\INCOMING" -t "2024-01 Val Thorens" -b 2024-01-27 -e 2024-02-04 -o "D:\MEDIA\JPG\TRAVEL" -n "Val Thorens"

# import a trip using EXIF dates instead of file time stamps, NOTE: VERY SLOW!
python psort.py -i "Z:\photos\INCOMING" -t "2024-02D Seahorse" -b 2024-02-07 -e 2024-02-24 -o "D:\MEDIA\JPG\TRAVEL" -n "Indonesia" --exif

# import "2023-12-24 xmas-eve"
python psort.py -i "Z:\photos\INCOMING" -s "2023-12-24 xmas-eve" -b 2023-12-24 -o "D:\MEDIA\JPG\HOME\2023"

# import all files from year 2024 
python psort.py -i "Z:\photos\INCOMING" -o "D:\MEDIA\JPG\HOME" --year 2024
```
# detailed functionality

## creation of destination directories
Destination directories are created automatically if they do not exist already. If destination directories do already exist, there is no error but a notification is given. 

## copy, move or mark?
By default **all** files from input source (-i) directory are copied to any of the destination directories. This means that the source files are left intact. This behavior can be changed by --date, --move or --mark options.

### date
When --date option is given, then operations are limited only to files created on and after the given date.

By default **all** files from input source (-i) directory are copied or moved (--move), unless the --date option limits this.

### move
If you give the -M or --move option, then the files are moved, which means that the source file is deleted after a copy to destination is completed. 

### nodup
By default any existing file at destination of the same name as at source is considered a duplicate and the copy/move is skipped and the file at destination is not touched, unless a --nodup option is given.  The --nopdup option causes the duplicate file to be copied/moved from source but renamed with a base name suffix of (1). For example the source file "photo.jpg" is renamed as photo(1).jpg and the existing file "photo.jpg" at destination is not touched.

### mark
If you give the "--mark FILE" option, then files copied from source are recorded into a "markfile". The full path to the "markfile" is given as FILE argument following --mark. When --mark option is given, then any previously copied files recoded to the markfile are skipped. This feature allows keeping files at source intact while allowing to keep track about what files have already been extracted to destinations.

As an example, the following command line will import files taken during year 2024 from Z:\photos\INCOMING to D:\MEDIA\JPG\HOME\2024 sorted by months but will skip any filenames contained in markfile Z:\photos\INCOMING\markfile.txt and filename of copied files will be added to the markfile.

```python psort.py -i "Z:\photos\INCOMING" -o "D:\MEDIA\JPG\HOME" --year 2024 --mark "Z:\photos\INCOMING\markfile.txt"```

The markfile is a plain text file, which contains on each line the full path filename inside double quotes, followed by space and a timestamp when the file was copied.

--mark option cannot be given when --move given.

## year
When you give -y or --year option, all the photos taken during a specific year are extracted such that photos taken in each month go into their own directory.

As an example, the following command line 

```python psort.py -i "Z:\photos\INCOMING" -o "D:\MEDIA\JPG\HOME" --year 2024```

Will create destination directory "D:\MEDIA\JPG\HOME\2024\01\" for all photos taken during January 2024, and "D:\MEDIA\JPG\HOME\2024\02\" for all photos taken during February 2024 and so forth. 

Before giving this command, you should consider first using the --special or --trip options to the source

## special
When you give -s or --special option the single day special event media file extraction is done. This allows you get all photos taken on a special one day event to a separate single directory with a single command.

As an example, the following command line 

```python psort.py -i "Z:\photos\INCOMING" -s "2023-12-24 xmas-eve" -b 2023-12-24 -o "D:\MEDIA\JPG\HOME\2023"```

creates a subdirectory

> "D:\MEDIA\JPG\HOME\2023\2023-12-24 xmas-eve\" 

Which will contain all media files taken on the date 2023-12-24, copied or moved from Z:\photos\INCOMING.


## trip
When you give -t or --trip option the trip media file extraction is done. This allows you get all photos from a trip or any special event that takes many days and have them organized per each day with a single command.

Extracts media files from input directory (specified by -i) that are taken between a range of dates (specified by -b and -e options) to a trip-specific subdirectory (string after -t) that is under output directory (string after -o). Media files are sorted by each day to a subdirectory under the trip subdirectory, such that the subdirectory has a name prefix (string after -n) and the date in YYYY-MM-DD format.

As an example, the following command line 

```python psort.py -i "Z:\photos\INCOMING" -t "2024-01 Val Thorens" -b 2024-01-27 -e 2024-01-28 -o "D:\MEDIA\JPG\TRAVEL" -n "Val Thorens"```

creates a trip subdirectory

> "D:\MEDIA\JPG\TRAVEL\2024-01 Val Thorens" 

and under this the following subdirectories:

> "D:\MEDIA\JPG\TRAVEL\2024-01 Val Thorens\Val Thorens 2014-01-27"
> "D:\MEDIA\JPG\TRAVEL\2024-01 Val Thorens\Val Thorens 2014-01-28"


