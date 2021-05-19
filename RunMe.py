import BuildXmlTtFromSource
import WriteXmlTt
import ParseXmlTt

# Provide the name of the spec file you wish to use.
# if __name__ == "__main__":
#     BuildXmlTtFromSource.BuildXmlTtFromSource('example_source_to_tt_spec')


# Provide the name of the TT you wish to write from a Json DB, the name of the .WTT file you want to create, whether we use a default category for trains with none.
# if __name__ == "__main__":
#     WriteXmlTt.Write_Full_Xml_Tt('Sheffield_-_Spring_2021', 'sheff_test', True)


# Provide the filepath and name of the file you wish to parse and whether you want to overwrite existing trains in the DB if present.
if __name__ == "__main__":
    ParseXmlTt.Parse_Full_Xml_Tt('newport_test.WTT', True, True)