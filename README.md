# SimsigTtTools
Some python scripts that can parse and write Simsig TTs.

### General Overview
Each TT that we either parse or generate from an external data source will be made up a set of TinyDB databases. 
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
    - With python packages:
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
Location: spec_files/source_to_xml_tt_specs/{file_name}.yaml
Purpose: Provides key properties for build a TT from source data
Example File: example_source_to_tt_spec.yaml

#### Train Categories Map
Location: spec_files/categories/{file_name}.yaml
Purpose: Used to set properties on each train that we write to a TT. Corresponds to Train Types in the in sim editor.
Example File: default_categories_map.yaml

To map charlwoodhouse trains the following properties are extracted from the page under the denoted field names:
![Category_fields](https://github.com/thejosmeister/SimsigTtTools/blob/master/assorted_files/Category_fields.png)

#### Locations Map
Location: location_maps/{sim_id}.txt
Purpose: Used to map the location names in the sim (mostly TIPLOC codes) to readable names as well as the sim entry points. (This will be revamped in future for usability)
Example File: newport.txt

#### Custom Location Logic
Location: spec_files/sim_custom_location_logic/{sim_id}.yaml
Purpose: Some locations in each sim require specific paths, lines, plats to be set to make TT data valid.
Example File: newport.yaml


## Main usages
Will provide an explanation/guide as to the main usages of the code.
There are example files in the repo for each of the spec file types. These will hopefully give a good idea of what is expected to be provided in them.

Warning: there is no validation of what you provide to the script so it can be quite likely that the script will seem to run ok only for the .WTT file to not to work in the sim.

### Take data from source and create .WTT file
You will need:
- Source to TT spec file - example at spec_files/source_to_xml_tt_spec/example_source_to_xml_spec.yaml
- Sim locations map - example at location_maps/newport.txt
- Train categories spec file - example at spec_files/train_categories/default_categories_map.yaml
- Custom location logic spec file - example at spec_files/custom_location_logic/newport.yaml

Actions:
Run BuildXmlTtFromSource in RunMe.py with arg ( <source to xml spec file name> )

Thus will produce a file xxx.WTT that will be a Simsig TT file, with the name specified in the spec file.

What happens:
Script will look for trains in the specified time window for all specified source locations. I.e. all trains at Newport from 0400 to 1800.
All trains will be converted to a Json representation of what they end up as in a Simsig TT. These Json trains are then stored in the Tinydb instance for the TT.
Alongside this, the other elements of the TT specified in the spec file (name, description, version) will also be stored in the Tinydb.

The script then converts all information in Tinydb instances to a .WTT file which is effectively a zip file containing two XML files with the TT data.

### Parse .WTT file into Json DB

### Making changes to Json TT
