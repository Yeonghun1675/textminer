#!/usr/bin/env python
# coding: utf-8

# In[19]:


import os
import regex as re
import json
import sys
import pandas as pd

from collections import Counter
from pathlib import Path
#from preprocessing import find_Abstract
from libs.utils import small_molecule_database, chemical_database
from libs.abbreviation import make_abbreviation
from libs.extract_paragraph_ver2 import test_paragraph, extract_paragraph, extract_paragraph_test
#rom extract_paragraph import *
from libs.extract_table import extract_table
from libs.extract_table_xml import extract_table_xml


# In[5]:


def extract_paragraph_battery(file_name, url_text=None, show_property=False, extract_all_property=False, return_file = False, parser = None):
    """Extract data from text (paragraph)
    ---------------------------------
    filename : (str) Name of file
    url_text : (str) Url of data (reference) (default : None, which is same as file_name)
    show_property : (bool) If True, print data (default : False)
    extract_all_property : (bool) If True, extract all of property. If false, extract only 'chracterization' and 'reaction' data
    return_documentTM : (bool) If True, return (json_list, Document_TM). Else, return (json_list) only
    parser : (str) html/pdf/xml parser for textmining ('cde_parser', 'elsevier_xml_parser')
    ---------------------------------
    output : json_list"""
    
    with open('./database/property_battery.json', 'r') as f:
        #pass
        unit_dict_OLED = json.load(f)
        
    with open("./database/abb_list_battery.json", 'r') as f:
        abb_list = json.load(f)
        ABB1, ABB2 = make_abbreviation(abb_list)
    with open("./database/smallmolecule.json", 'r') as f:
        sm_database = json.load(f)
        sm1, sm2 = small_molecule_database(sm_database)
    with open("./database/chemical_battery.json", 'r') as f:
        cm_database = json.load(f)
        cm1, cm2 = chemical_database(cm_database)
    with open("./database/solvent_list.json", 'r') as f:
        solvent_list = json.load(f)
    solvent_re = r"|".join(solvent_list)
    with open("./database/exclude_battery.json", 'r') as f:
        exclude = json.load(f)
    
    database = {'ABB1':ABB1, 'ABB2':ABB2, 'sm1':sm1, 'sm2':sm2, 'chemname':cm1, 'chemhash':cm2, 'exclude':exclude}
    float_re = r"[+-]?\d+\.?\d*"
    special_unit_dictionary = {'pH' : r"pH\s?(?P<NUM>[+-]?\d+[.]?\d*)"}
    
    
    return extract_paragraph(file_name, url_text = url_text, database = database, show_property=show_property, return_documenTM=return_file,
                                                      special_unit_dictionary=special_unit_dictionary, extract_all_property=extract_all_property, 
                                                      unit_dict = unit_dict_OLED, parser = parser)


# In[9]:


def extract_table_battery(filename, url_text=None, show_data=False, write_rawfile=False, output_filename=None, parser = None):
    """Extract data from table
    ---------------------------------
    filename : (str) name of file
    url_text : (str) url of data (reference)
    show_data : (bool) if True, print data
    write_rawfile : (bool) if True, write raw file
    output_filename : (str) name of output file (when write_rawfile is True)
    parser : (str) html/pdf/xml parser for textmining ('cde_parser', 'elsevier_xml_parser')
    ---------------------------------
    output : json_list"""
    
    if parser == 'elsevier_xml_parser':
        return extract_table_xml(filename, url_text, show_data, write_rawfile, output_filename, reader = 'elsevier')
        
    
    return extract_table(filename, url_text, show_data, write_rawfile, output_filename)


# In[10]:


def to_pd(file_name, url_text = None, show = False, extract_all_property = False, write_table_raw = False, parser = None):
    
    text_data = extract_paragraph_battery(file_name, url_text = url_text, show_property=show, extract_all_property=extract_all_property,
                                         parser = parser)
    table_data = extract_table_battery(file_name, url_text = url_text, show_data=show, write_rawfile = write_table_raw, parser=parser)
    
    data_list = []
    
    def clean_data(data, data_from = None):
        Material = data.get('Material')
        Property = data.get('Property')
        Value = data.get('Value')
        Unit = data.get('Unit')
        Condition = data.get('Condition')
        Condition = str(Condition)
        Caption = data.get('Caption')
        Footnote = data.get('Footnote')
        
        if not Unit:
            unit_match = re.match(r"^(?P<property>.+)\((?P<unit>.+)\)$", Property)
            if unit_match:
                Unit = unit_match.group("unit").strip()
                Property = unit_match.group("property").strip()  
                
        return [Material, Property, Value, Unit, data_from, Condition, Caption, Footnote]
        
    for data in text_data:
        cleaned_data = clean_data(data, 'Text')
        data_list.append(cleaned_data)
    for data in table_data:
        cleaned_data = clean_data(data, 'Table')
        data_list.append(cleaned_data)
        
    return pd.DataFrame(data_list, columns=['Material', 'Property', 'Value', 'Unit', 'Data from', 'Condition', 'Caption', 'Footnote'])   


# In[11]:


if __name__ == '__main__':
    arg = sys.argv
    assert len(arg)-1, "There are no file name"
    file_name = arg[1]
    url_text = None
    show = False
    extract_all_property = False
    write_table_raw = False
    task_all = False
    
    if '--help' in arg:
        print ("""OLED Textmining code
>> python extract_OLED.py input_file (output_file) (options)

Default of output_file is 'output.csv'

Options:
--show (-s) : print all progress and data
--extractall (-e) : extract all possible units in text
--rawfile (-r) : make .raw file of table data
--all (-a) : run code for all .html files in input_folder.
             outputs are generated at './output' folder
             >> python extract_OLED.py input_direc -a
--url (-u) : write reference of data 
             >> python extract_OLED.py input_file (output_file) --url reference_name
""")
        sys.exit()
    
    try:
        temp_out = arg[2]
        if not re.match(r"^-", temp_out):
            output = temp_out
        else:
            output = 'output.csv'
    except:
        output = 'output.csv'
        
    for i, key in enumerate(arg[2:]):
        if key == "--show" or key == '-s':
            show = True
        elif key == "--extractall" or key == '-e':
            extract_all_property = True
        elif key == '--rawfile' or key == '-r':
            write_table_raw = True
        elif key == '--url' or key == '-u':
            url_text = arg[i+1]
            
        elif key == '--all' or key == '-a':
            task_all = True
            files = Path(file_name)
            assert files.is_dir(), "Not directory"
            file_htmls = files.glob("*.html")
            output_folder = Path("./output")
            if not output_folder.exists():
                output_folder.mkdir()
            
    if task_all:
        for file_name in file_htmls:
            output_filename = output_folder/file_name.name.replace(".html", ".csv")
            pd_out = to_pd(file_name, url_text, show, extract_all_property, write_table_raw)
            pd_out.to_csv(output_filename)

    else:
        pd_out = to_pd(file_name, url_text, show, extract_all_property, write_table_raw)
        pd_out.to_csv(output)

