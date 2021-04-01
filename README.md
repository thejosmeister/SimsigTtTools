# SimsigTtTools
Will hopefully become comething that can parse and write Simsig TTs via python

### General Overview
Each TT will have a set of TinyDB databases. 
The data in the db will be a Json representation of what you would find in a Simsig XML TT (the upackaged files from a .WTT file).

Whenever we fetch input information from an external source (RTT, charlwoodhouse, NROD) we will translate that to the Json representation and store in a db.

There is functionality to write the Json data in the db as an XML TT and then package it into a .WTT file.
We can parse an XML TT to Json data in the db as well.

Beyond this there is/will be various functions to edit the TT data in a more flexible way than via the in sim TT editor. 
Note, in sim editor functionality can still be used by writing to XML, making changes in sim and then parsing again. 

## Main usages
Will provide an explanation/guide as to the main usages of the code.

### Take data from source and create .WTT file
You will need:
- Source to TT spec file
- Sim locations map
- Train categories spec file
- Custom location logic spec file

Actions:
Run xxx in yyy.py with args ( tt name, sim id, spec location )

Thus will produce a file xxx.WTT that will be a Simsig TT file.

What happens:
Script will look for trains in the specified time window for all specified source locations. I.e. all trains at Newport from 0400 to 1800.
All trains will be converted to a Json representation of what they end up as in a Simsig TT. These Json trains are then stored in the Tinydb instance for the TT.
Alongside this, the other elements of the TT specified in the spec file (name, description, version) will also be stored in the Tinydb.

The script then converts all information in Tinydb instances to a .WTT file which is effectively a zip file containing two XML files with the TT data.

### Parse .WTT file into Json DB

### Making changes to Json TT
