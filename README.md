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
| **o** | output  | output directory                                                |
| **t** | trip    | do trip sorting, give trip label                                |
| **n** | name    | for trip sorting daily prefix label                             |
| **s** | special | special date extraction, give date in b arg                     |
| **b** | begin   | begin date of the trip or special event date, format YYYY-MM-DD |
|       | batfile | create BAT file, instead of executing moves                     |
| **e** | end     | end date of the trip, format YYYY-MM-DD                         |
| **d** | dryrun  | dry run, nothing touched                                        |
| **y** | year    | year to extract YYYY                                            |
| **r** | report  | report only                                                     |
| **z** | zort    | report files sorted by dates                                    |
|       | summary | summary of years, months, days                                  |
|       | exif    | use EXIF date instead of file timestamp                         |
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
