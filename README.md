# SimsigTtTools
Some python scripts that can parse and write Simsig TTs.

### General Overview
Each TT that we either parse or generate from an external data source will be made up a set of [TinyDB](https://tinydb.readthedocs.io/en/latest/getting-started.html) databases. 
The data in the DBs will be a Json representation of what you would find in a Simsig XML TT (the upackaged files from a .WTT file).

Whenever we fetch input information from an external source (RTT, charlwoodhouse, NROD) we will translate that to the Json representation and store in a db.

There is functionality to take the Json data in the DBs for a particular timetable, write it as an XML TT and then package it into a .WTT file.

We can also parse an XML TT to Json data in the db as well.

The idea around structuring the code like this is that we can use various functions to edit the TT data in a more flexible way than via the in sim TT editor.
There is also scope for using the Json data to provide more in depth TT analysis and reports (pathing diagrams, location reports etc.)

Note, in sim editor functionality can be used in conjunction with the code. 
This would entail writing the TT to XML making changes in sim and then parsing again. 

### Requirements 
- Python 3 - definitely works with v3.7 or higher, probably works for earlier versions
    - Non standard python packages:
        - [tinydb](https://tinydb.readthedocs.io/en/latest/getting-started.html)
        - [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
        - [requests](https://pypi.org/project/requests/)
        - [PyYAML](https://pypi.org/project/PyYAML/)
- some basic coding knowledge - will need to run functions with your own arguments i.e. calling ParseXmlTt(<specified args>)
- text editor like notepad++ - used for editing yaml spec files
- source data from real time trains or charlwoodhouse (other sources may be integrated in future)

### File Structure

The file structure of the repo is deliberately flat with respect to the .py files as it can be a dark art trying to get the python interpreter to import other .py files from another directory.
Here is a brief guide:

File struct:
Directories present for spec/templates:
```
/db/{tt_name}/main_header.json                                # Location of Json TT data
   |            /rules.json
   |            /train_tts.json 
   /{tt_name}/main_header.json
   |            /rules.json
   |            /train_tts.json
   ...
/location_maps/{sim_id}_locations.txt                         # Location of sim location maps
             /{sim_id}_locations.txt
             ...
/templates/tt_templates/defaultTimetableNoEP.txt
          |            /defaultTimetableSeedPoint.txt
          |            /defaultTimetableWithEntryPoint.txt
          /activity_templates/crewChangeTemplate.txt
                             /detatchFrontTemplate.txt
                             /detatchRearTemplate.txt
                             ...
/spec_files/categories/default_cat_map.txt                    # Location of train category maps
           |          /train_categories_1.xml
           |          ...
           /source_to_xml_tt_specs/{tt_name}.yaml             # Location of data source to .WTT file specs
           |                      /{tt_name}.yaml
           |                      ...
           /sim_custom_location_logic/{sim_id}.yaml           # Location of sim custom logig definitions
                                     /{sim_id}.yaml
                                     ...
BuildXmlTtFromSource.py - Creates a .WTT file from a data source such as rtt using a source_to_xml_tt_spec yaml file
WriteXmlTt.py - Creates a .WTT file from data already in TinyDB form
ParseXmlTt.py - Parses SavedTimetable.xml from .WTT file in to TinyDB instance
parseData.py - handles parsing of source data
customLocationLogic.py - handles custom sim location logic which is used when creating a TT from external data source
common.py - contains some common code
```

### Key Spec Files
#### Source To XML TT Spec
- **Location:** spec_files/source_to_xml_tt_specs/{file_name}.yaml
- **Purpose:** Provides key properties for build a TT from source data
- **Example File:** example_source_to_tt_spec.yaml

#### Train Categories Map
- **Location:** spec_files/categories/{file_name}.yaml
- **Purpose:** Used to set properties on each train that we write to a TT. Corresponds to Train Types in the in sim editor.
- **Example File:** default_categories_map.yaml

To map charlwoodhouse trains, the following properties are extracted from the page under the denoted field names. Notes in the example file explain how you can match trains to these values:
![Category_fields](https://github.com/thejosmeister/SimsigTtTools/blob/master/assorted_files/Category_fields.png)

#### Locations Map
- **Location:** location_maps/{sim_id}.txt
- **Purpose:** Used to map the location names in the sim (mostly TIPLOC codes) to readable names as well as the sim entry points. (This will be revamped in future for usability)
- **Example File:** newport.txt

#### Custom Location Logic
- **Location:** spec_files/sim_custom_location_logic/{sim_id}.yaml
- **Purpose:** Some locations in each sim require specific paths, lines, plats to be set to make TT data valid.
- **Example File:** newport.yaml


## Main usages
The things that can be done using the code. Use the RunMe.py file to execute code (or your own runner file).

Warning: there is no validation of what you provide to the script so it can be quite likely that the script will seem to run ok only for the .WTT file to not to work in the sim.

### Take data from source and create .WTT file
**You will need:**
- Source To XML TT Spec file
- Train categories spec file
- Locations Map file for the particular sim
- Custom location logic file

**Actions:**
Run BuildXmlTtFromSource.BuildXmlTtFromSource in RunMe.py with arg ( <source to xml spec file name> )

This will produce a file xxx.WTT that will be a Simsig TT file, with the name specified in the spec file.

**What happens:**
The code will look for trains in the specified time window for all specified source locations. I.e. all trains at Newport from 0400 to 1800.
All trains will be converted to a Json representation of what they end up as in a Simsig TT. These Json trains are then stored in the Tinydb instance for the TT.
Alongside this, the other elements of the TT specified in the spec file (name, description, version) will also be stored in the Tinydb.

The script then converts all information in Tinydb instances to a .WTT file which is effectively a zip file containing two XML files with the TT data.

**Notes:**

If want to create a new TT with the same name as an old one (or overwite all trains from the last) then make sure you delete the DB files to avoid old data not being left around.

It is assumed that all trains fetched from a location are on the same day i.e. the charlwoodhouse location pages show trains from 0400 on day 1 to 0400 on day 2. If you set the times to start_time: 0000 and end_time: 2400 then the code will take the trains from 0000 to 0400 on day 2 as day 1 trains.

There are a number of things that will require manual editing after creating the .WTT file:
- Trains that leave and enter the sim more than once will need separate copies for the stages of their journey through the sim.
- Next workings, splits and joins will have to be added in. (Next workings can be pretty quickly done using the in sim editor tools)
- More specific train categoies/types will have to be selected.
- Freight headcodes and some properties (e.g. length) will need to be input/respecified (placeholder headocdes like 6ADJ are added by the code to indicate no headcode)
- Some non standard locations not caught in custom logic will need to be modified for some trains.

### Parse .WTT file into Json DB
**You will need:**
- Locations Map file for the particular sim

**Actions:**
Run ParseXmlTt.Parse_Full_Xml_Tt in RunMe.py with arg ( <.WTT filepath and name>, <True if you want to overwrite existing trains in the TT DB, False if not> )

**What happens:**
The code will populate a set of Json TT DBs under the filepath db/{parsed_TT_name}.

All trains will be converted to a Json representation of what they end up as in a Simsig TT and placed into the train_tts.json database file. Timetable header information will be in the main_header.json DB file. Any rules will be in the rules.json DB file.

Methods in the dbClient.py file can be used to query and modify data in the Json DBs.


### Write info strored in Json DB to a .WTT file
**You will need:**
- Locations Map file for the particular sim

**Actions:**
Run WriteXmlTt.Write_Full_Xml_Tt in RunMe.py with arg ( <tt name that DB files are under>, <name of .WTT file we will write to>, <True if you want to use a default train category for trains that dont have one, False if not> )

**What happens:**
The code will take data in the named set of DB files and write it to a .WTT file with the specified name. This is done automatically in the BuildXmlTtFromSource method.

## Making changes to Json TT

More funtions will be added to make useful changes to TTs like bulk rules writing, bulk train editing, more indepth reports.
