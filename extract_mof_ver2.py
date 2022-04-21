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
from libs.extract_paragraph_ver2 import extract_paragraph
#rom extract_paragraph import *
from libs.extract_table import extract_table
from libs.extract_table_xml import extract_table_xml


# In[5]:


def extract_paragraph_mof(file_name, url_text=None, show_property=False, extract_all_property=False, 
                          return_file = False, parser = None):
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
    
    with open('./database/MOF/property_MOF.json', 'r') as f:
        #pass
        unit_dict_OLED = json.load(f)
        
    with open("./database/MOF/abb_list.json", 'r') as f:
        abb_list = json.load(f)
        ABB1, ABB2 = make_abbreviation(abb_list)
    with open("./database/MOF/smallmolecule.json", 'r') as f:
        sm_database = json.load(f)
        sm1, sm2 = small_molecule_database(sm_database)
    with open("./database/MOF/chemical.json", 'r') as f:
        cm_database = json.load(f)
        cm1, cm2 = chemical_database(cm_database)
    with open("./database/MOF/solvent_list.json", 'r') as f:
        solvent_list = json.load(f)
    solvent_re = r"|".join(solvent_list)
    with open("./database/MOF/exclude.json", 'r') as f:
        exclude = json.load(f)
    
    database = {'ABB1':ABB1, 'ABB2':ABB2, 'sm1':sm1, 'sm2':sm2, 'chemname':cm1, 'chemhash':cm2, 'exclude':exclude}
    float_re = r"[+-]?\d+\.?\d*"
    special_unit_dictionary = {'pH' : r"pH\s?(?P<NUM>[+-]?\d+[.]?\d*)"}
    
    
    return extract_paragraph(file_name, url_text = url_text, database = database, show_property=show_property, return_documenTM=return_file,
                             extract_all_property=extract_all_property, unit_dict = unit_dict_OLED, parser = parser)


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
