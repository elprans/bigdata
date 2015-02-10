README File for Census 2000 Summary File 1 Delivered via FTP

Note:  We are unable to provide one-on-one support for applications of the data to 
specific spreadsheets or data base software.  However, we do have detailed 
instructions on loading an ASCII  file into Access97 at 
www.census.gov/support/SF1ASCII.html.  On some systems, there may be a request for 
a password.  If this happens, select cancel.  You should immediately go to the site.      

About the FTP Application

This FTP (File Transfer Protocol) application is intended for experienced users 
of census data, compressed files, and spreadsheet/database software. It provides 
quick access to data users, such as State Data Centers and news media, who need 
to begin their analysis immediately upon data release. Due to the size of the 
files, the FTP user should have a fast file transfer capability. 

Each state directory provides all files available for the identified state. Once 
uncompressed, the data are in a flat ASCII format.  The geographic file is in a 
fixed-field format; the two data files are in comma delimited format. No 
software is provided. Users of the FTP application need to unzip the compressed 
file after downloading, then import it into the spreadsheet/database software of 
their choice for data analysis and table presentation.

Other Sources of the Data

The Census Bureau releases most Census 2000 data on a state-by-state basis. 
Tables generally are available in American FactFinder (factfinder.census.gov) 
the day of the release of the designated state file. Within American FactFinder, 
individual tables can be downloaded in a text delimited or comma delimited 
format.  

For users without immediate need for the data, CD-ROMs containing the data and 
access software are scheduled for shipping shortly after the state file release.  
They can be ordered from the Census Bureau's Customer Services Center at 301-
457-4100.  

FTP File Transfer

The FTP directory for Summary File 1 (SF1) is at  
ftp2.census.gov/census_2000/datasets/Summary_File_1 .  When the SF1 data are 
added to the respective state directories, there will be 40 files for each 
state-- a geographic header file and thirty-nine data files.  See the chart 
below for more information on the data segments.

To facilitate transferring multiple files, we suggest using features commonly 
found in most vendor's FTP utility.  In the UNIX environment, the "mget" 
subcommand allows transferring multiple files using a wildcard character.  For 
example, once you have navigated into the SF1 directory for Nebraska, you can 
download all 40 SF1 files with the following two ftp subcommands: 

ftp>prompt off		(to avoid being asked for verification of each file, 
optional)
ftp>mget ne*

When testing the download in a PC environment, we used the ws_ftp  product.  
This product, and many other FTP products developed for the PC environment, 
allows individual multiple file selection using the control key or block 
multiple file selection using the shift key.  

File Naming Conventions

File naming conventions have changed since the release of the Redistricting 
data.  The new convention is ss000yy_uf1.zip  where ss is the USPS state 
abbreviation and yy is the number (01-39) of the file segment.  The geoheader 
file name is ssgeo_uf1.zip .
   
File Information

Once uncompressed, these files are in flat ASCII format. The geographic header 
file (see below) contains fixed fields while the data files (File01 through 
File39, see below), including the geographic link fields, are in comma-delimited 
format.  These files have been constructed in a UNIX environment. They use an 
ASCII linefeed, chr(10), to indicate a new record.

For successful use with many programs running in a Windows environment, these 
files need to be modified to use the ASCII carriage return/linefeed sequence, 
chr(13) + chr(10) as a record terminator. This is an easy step in the UnZIP 
process using any UnZIP software which offers the conversion option.  We tested 
PKZIP for Windows, version 4.00 following the steps outlined below.  This PKZIP 
shareware can be downloaded from www.pkware.com.  After installing PKZIP, do the 
following:

	--Select the file 

	--Select the Extract option on the tool bar

	--Select the options button at the bottom of the Extract page

		--Under the Miscellaneous section, select the "DOS - convert to 
CR/LF"
	
The resulting file will meet the ANSI MS-DOS/Windows standard used by Access 97 
and other MS Windows-based programs.  If the data are being processed in a UNIX 
environment, they can be unzipped using any standard ZIP/UnZIP package.

These FTP data are available as compressed files at the 90% (approximately) file 
compression ratio. If you are using a modem/telephone line link to the Internet, 
we do not recommend using the FTP option.

Segmented Data 

The data in the redistricting files and other Census 2000 summary files are 
segmented. This is done so that individual files will not have more than 255 
fields, facilitating exporting into spreadsheet or database software. In short, 
to get the complete data set for SF1 files, users must FTP all forty files in 
the state directory.   

These test files contain:

	

File Name  Number of Data Items   Starting Matrix      Ending Matrix 

01                222                   P1                    P5

02                238                   P6                    P18

03                236                   P19                   P33

04                149                   P34                   P45

05                245                   P12A                  P12E

06                241                   P12F                  P16I

07                234                   P17A                  P27C

08                247                   P27D                  P28E

09                244                   P28F                  P30H

10                229                   P30I                  P34I

11                180                   P35A                  P35I

12                235                   PCT1                  PCT9

13                 45                   PCT10                 PCT11

14                209                   PCT12                 PCT12

15                203                   PCT13                 PCT17

16                209                   PCT12A                PCT12A

17                209                   PCT12B                PCT12B

18                209                   PCT12C                PCT12C

19                209                   PCT12D                PCT12D

20                209                   PCT12E                PCT12E

21                209                   PCT12F                PCT12F

22                209                   PCT12G                PCT12G

23                209                   PCT12H                PCT12H

24                209                   PCT12I                PCT12I

25                209                   PCT12J                PCT12J

26                209                   PCT12K                PCT12K

27                209                   PCT12L                PCT12L

28                209                   PCT12M                PCT12M

29                209                   PCT12N                PCT12N

30                209                   PCT12O                PCT12O

31                245                   PCT13A                PCT13E

32                235                   PCT13F                PCT15C

33                228                   PCT15D                PCT17B

34                225                   PCT17C                PCT17E

35                225                   PCT17F                PCT17H

36                 75                   PCT17I                PCT17I

37                217                     H1                    H20

38                207                     H11A                  H15I

39                171                     H16A                  H16I


It is easiest to think of the file set as a logical file.  However, this logical 
file consists of forty physical files: the geographic header file and file01-
file39. This structure is a change from previous decennial census files.    

The explanation below for linking the summary file 1 files requires specific 
location information for the geographic header.  These are located in chapter 7 
of the technical documentation www.census.gov/prod/cen2000/doc/sf1.pdf .  A 
unique logical record number (LOGRECNO in the geographic header) is assigned to 
all files for a specific geographic entity; all records for that entity can be 
linked together across files.  Additional identifying fields are also carried 
over from the geographic header file to the table files.  These are file 
identification (FILEID), state/U.S. abbreviation (STUSAB), characteristic 
iteration (CHARITER), characteristic iteration file sequence number (CIFSN).  

The geographic header record layout is identical across all electronic data 
products from Census 2000.  Since the SF1 files are relatively simple, some of 
the fields, including some geographic header fields that appear in all forty 
files (geographic header, file01-file39)  are not used.  For example, the 
character iteration (CHARITER) field is only used in SF2/SF4.  In SF1, it is 
always coded as 000.

File Record Layout

For a layout of the individual tables for each file, see  
www.census.gov/prod/cen2000/doc/sf1.pdf . Select Chapter 6, Summary Table 
Outlines.  

Spreadsheet and Data Base Aids

We are unable to provide one-on-one support for applications of the data to 
specific spreadsheets or data base software.  However, we do have detailed 
instructions on loading an ASCII  file into Access97 at 
www.census.gov/support/SF1ASCII.html    


Estimated File Sizes

These size estimates are for the total file package for SF1.  


State	     	         SF1

	                                   GeoHeader and File01-File39

			unzipped	                  zipped
				
						
Alabama	1.7G		87M								

Alaska	.3G			13M						
	
Arizona	1.5G		75M		

Arkansas	1.5G		75M

California	5.1G	260M			

Colorado	1.5G		75M	

Connecticut	.6G		28M			

Delaware	.2G		10M	

District of 
       Columbia	.6G		30M

Florida	3.4G		170M

Georgia	2.3G		110M

Hawaii	.2G		10M		

Idaho	.9G		45M

Illinois	4.1G		209M

Indiana	2.1G		108M

Iowa	1.7G		86M

Kansas	1.7G		88M		

Kentucky	1.1G		58M

Louisiana	1.5G		77M		

Maine	.5G		25K

Maryland	.9G		44M			

Massachusetts	1.2G		58M		

Michigan	2.7G		136M

Minnesota	2G		105M		
	
Mississippi	1.4G		70M		

Missouri	2.5G		125M	
	
Montana	.9G		45M

Nebraska	1.4G		70M		

Nevada	.7G		34M		

New     
    Hampshire	.3G		16M		

New Jersey	1.7G		82M	

New Mexico	1.4G		68M	

New York	3.6G		180M		

North Carolina	2.5G		123M		

North Dakota	.9G		42M

Ohio	2.8G		138K			

Oklahoma	1.8G		90M	

Oregon	1.4G		71M		

Pennsylvania	                   3.5G	174M		

Rhode Island	.24G		12M	

South Carolina	1.5G		75M		

South Dakota	.8G		42M	
	
Tennessee	1.9G	95M		

Texas	6.8G	340M		

Utah	.8G	41M			

Vermont	.25G	12M		

Virginia	1.5G	77M		

Washington	2G	100M		

West Virginia	.9G	44.2M				

Wisconsin	2G	100M

Wyoming 	.7G	32M
		
Puerto Rico	.8G	36M		
1 This is the number in field CIFSN, beginning in position 17.




 

 

