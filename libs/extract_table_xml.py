import os
import re
import string
import types
import json, ast
import copy
from chemdataextractor import Document
from chemdataextractor.doc.text import Paragraph, Title, Heading, Citation, Footnote
from chemdataextractor.doc.table import Table
from chemdataextractor.nlp.tokenize import ChemWordTokenizer
from bs4 import BeautifulSoup


def isBlank (myString):
	if myString and myString.strip():
		#myString is not None AND myString is not empty or blank
		return False
	#myString is None OR myString is empty or blank
	return True

def removeDuplicates(listofElements):

	# Create an empty list to store unique elements
	uniqueList = []

	# Iterate over the original list and for each element
	# add it to uniqueList, if its not already there.
	for elem in listofElements:
		if elem not in uniqueList:
			uniqueList.append(elem)

	# Return the list of unique elements
	return uniqueList

def tuple_sum(listofElements):
	temp_text = ''
	for elem in listofElements:
		if listofElements[len(listofElements)-1] == elem:
			temp_text = temp_text + elem
		else:
			temp_text = temp_text + elem + ' '
	return temp_text

def word_list_revise(listofWords,chemical_list):
	crit = 0
	crit2 = len(listofWords) - 1
	while crit != crit2 and len(listofWords) != 0:
		if any((listofWords[crit] +' '+ listofWords[crit+1]) in s for s in chemical_list):
			listofWords[crit] = listofWords[crit] +' '+ listofWords[crit+1]
			del listofWords[crit+1]
			crit2 -= 1
		else:
			crit += 1
	return listofWords

def clean_text(text):
	unicode_list1=['\n', '&nbsp;', '\u2009', '\t', '\xa0', '\u2008', '\u2007']# unicode list of space
	unicode_list2=['\u202f', '\u205f', '\u200a'] # unicode list of waste
	for i in range(len(unicode_list1)):
		text = text.replace(unicode_list1[i],' ')
	for i in range(len(unicode_list2)):
		text = text.replace(unicode_list2[i],'')

	#Delete useless html tag part
	soup = BeautifulSoup(text, 'html.parser')
	text = soup.get_text()

	#Delete duplicated spaces
	text = " ".join(text.split())
	return text

def is_digit(text):
	try:
		tmp = float(text)
		return True
	except ValueError:
		return False

def ischemical(text,Chemlist):
	crit = False
	if Document(text).cems != []:
		crit = True
	for i in range(len(Chemlist)):
#		print (Chemlist[i],"\t",text)
		if Chemlist[i].find(text) != -1:
			crit = True
#			print ("crit1")
			break
		elif len(Chemlist[i]) > 2 and text.find(Chemlist[i]) != -1:
			crit = True
#			print ("crit2")
			break
	return crit

def chem_percentage(text,Chemlist):
	chemper = 0
	tmp2 = re.split('[\s/]+',text)
	for i in range(len(tmp2)):
		if ischemical(tmp2[i],Chemlist) == True:
			chemper += 1/len(tmp2)
	return chemper



def statistics(export_data):
	Name = ['Temperature','Precursor Ratio','Synthesis Time','Particle Size','Surface Area','Cycle Retention Stability','Voltage','Conductivity','Diffusion Coefficient','Capacity','Band Gap','Activation Energy']
	Unit = ['K','\d:\d','h','nm','m2 g-1','%','V','S cm-1','cm2 s-1','m Ah g-1|m Ah cm-3|Ah kg−1','eV','kJ/mol']
	Regex = ['[tT]emper','[Pp]recursor','[Tt]ime','[Pp]article [Ss]ize|Size','[Ss]urface area|SA|BET','[Cc]ycle [Rr]etention|[Rr]etention','Voltage|\sV\s','[Cc]onducti','[Dd]iffus','[Cc]apacit','[Bb]and [Gg]ap','[Aa]ctivation [Ee]nergy|E[Aa]']
	Tag = ['T','PR','ST','PS','SA','CRS','V','IC','DC','C','BG','AE']
	Num = [0,0,0,0,0,0,0,0,0,0,0,0]
	for i in range(len(export_data)):
		taged = 0
		for j in range(len(Name)):
			prop_regex = re.compile(Regex[j])
			unit_regex = re.compile(Unit[j])

#			print (prop_regex.search(export_data[i].split(" ★ ")[1]), unit_regex.search(export_data[i].split(" ★ ")[1]))
			if taged == 0 and prop_regex.search(export_data[i].split(" ★ ")[1]):# or unit_regex.search(export_data[i].split(" ★ ")[1]):
				export_data[i] = export_data[i] + " ★ " + Tag[j]
				taged = 1
				Num[j] = Num[j] + 1
		if taged == 0:
		 	export_data[i] = export_data[i] + " ★ NONE"
	return [export_data, Num]
# Transform to KIST type json
def transform_kist(json_list,url_text):
	Properties = ['Composition','Promoter','Surface area','Active site area','Porosity','Pore volume','Acidity','Basicity','Adsorption energy','Diffusivity','Optical band gap','Conversion','Yield','Productivity','Selectivity','Faradaic efficiency','Turnover frequency','Rate constant','Recyclability','Activity']
	Regex = ['composit|ratio|.*wt\%','Promot','surface area|SA|BET|SBET','.*Active','Porosity','Pore volume|PV|poreV|Vto','Acidity','Basicity','Adsorption energy|Ads energy|Binding energy|AdsorptionE','Diffus','band gap','Conversion','yield','Productiv','selectiv','Fradaic efficiency|Faradaic','Turnover frequency|TOF|Turn over frequency','rate constant|rate','recyclab','.*Activity']
	JSON = []
	temp = dict()
	initial_json = dict()
	material_list = []

	temp["_id"] = ""
	temp["docid"] = ""
	temp["catalyst"] = ""
	temp["Synthesis"] = dict()
	temp["Synthesis"]["Synthesis_Condition"] = ""
	temp["Characterization_Data"] = dict()
	temp["Characterization_Data"]["Catalyst_Composition"] = []
	temp["Characterization_Data"]["Catalyst_Microstructure"] = []
	temp["Characterization_Data"]["Support_Composition"] = []
	temp["Characterization_Data"]["Support_Microstructure"] = []
	temp["Characterization_Data"]["Promoter"] = []
	temp["Characterization_Data"]["Specific_Surface_Area"] = []
	temp["Characterization_Data"]["Microporous_Surface_Area"] = []
	temp["Characterization_Data"]["Active_Site_Area_By_Chemisorption"] = []
	temp["Characterization_Data"]["Porosity"] = []
	temp["Characterization_Data"]["Total_Pore_Volume"] = []
	temp["Characterization_Data"]["Micropore_Volume"] = []
	temp["Characterization_Data"]["Acidity"] = []
	temp["Characterization_Data"]["Basicity"] = []
	temp["Characterization_Data"]["Adsorption_Energy"] = []
	temp["Characterization_Data"]["Diffusivity_On_Support"] = []
	temp["Characterization_Data"]["Optial_Band_Gap"] = []
	temp["Characterization_Raw_Data"] = dict()
	temp["Characterization_Raw_Data"]["XRD_Spectra"] = ""
	temp["Characterization_Raw_Data"]["XPS_ESCA_Spectra"] = ""
	temp["Characterization_Raw_Data"]["TEM"] = ""
	temp["Characterization_Raw_Data"]["SEM"] = ""
	temp["Characterization_Raw_Data"]["EDS_WDS"] = ""
	temp["Characterization_Raw_Data"]["UV_VIS_Spectra_WDS"] = ""
	temp["Characterization_Raw_Data"]["FTIR"] = ""
	temp["Characterization_Raw_Data"]["Raman"] = ""
	temp["Characterization_Raw_Data"]["XAFS"] = ""
	temp["Characterization_Raw_Data"]["XANES"] = ""
	temp["Characterization_Raw_Data"]["TPD_TPO_FPR"] = ""
	temp["Characterization_Raw_Data"]["BET_Isotherm"] = ""
	temp["Characterization_Raw_Data"]["Chemisorption"] = ""
	temp["Characterization_Raw_Data"]["TGA"] = ""
	temp["Characterization_Raw_Data"]["ICP"] = ""
	temp["Characterization_Raw_Data"]["DOS"] = ""
	temp["Reaction"] = []
	reaction = dict()

	reaction["Performance_Test_Method"] = []
	method = dict()

	method["Reactants"] = ""
	method["Products"] = ""
	method["Reactant_Datagram"] = ""

#	reaction["Performance_Test_Method"].append(method)
	reaction["Performance_Data"] = dict()
	reaction["Performance_Data"]["Temperature"] = dict()
	reaction["Performance_Data"]["Temperature"]["unit"] = ""
	reaction["Performance_Data"]["Temperature"]["number"] = 0.0

	reaction["Performance_Data"]["Pressure"] = dict()
	reaction["Performance_Data"]["Pressure"]["unit"] = ""
	reaction["Performance_Data"]["Pressure"]["number"] = 0.0

	reaction["Performance_Data"]["Reaction_Time"] = dict()
	reaction["Performance_Data"]["Reaction_Time"]["unit"] = ""
	reaction["Performance_Data"]["Reaction_Time"]["number"] = 0.0

	reaction["Performance_Data"]["Applied_Voltage"] = dict()
	reaction["Performance_Data"]["Applied_Voltage"]["unit"] = ""
	reaction["Performance_Data"]["Applied_Voltage"]["number"] = 0.0

	reaction["Performance_Data"]["TurnOver_Frequency"] = dict()
	reaction["Performance_Data"]["TurnOver_Frequency"]["unit"] = ""
	reaction["Performance_Data"]["TurnOver_Frequency"]["number"] = 0.0

	reaction["Performance_Data"]["TurnOver_Number"] = dict()
	reaction["Performance_Data"]["TurnOver_Number"]["unit"] = ""
	reaction["Performance_Data"]["TurnOver_Number"]["number"] = 0.0

	reaction["Performance_Data"]["Rate_Constant"] = dict()
	reaction["Performance_Data"]["Rate_Constant"]["unit"] = ""
	reaction["Performance_Data"]["Rate_Constant"]["number"] = 0.0

	reaction["Performance_Data"]["Yield"] = dict()
	reaction["Performance_Data"]["Yield"]["unit"] = ""
	reaction["Performance_Data"]["Yield"]["number"] = 0.0

	reaction["Performance_Data"]["Productivity_Yield"] = dict()
	reaction["Performance_Data"]["Productivity_Yield"]["unit"] = ""
	reaction["Performance_Data"]["Productivity_Yield"]["number"] = 0.0

	reaction["Performance_Data"]["Specific_Activity"] = dict()
	reaction["Performance_Data"]["Specific_Activity"]["unit"] = ""
	reaction["Performance_Data"]["Specific_Activity"]["number"] = 0.0

	reaction["Performance_Data"]["Mass_Activity"] = dict()
	reaction["Performance_Data"]["Mass_Activity"]["unit"] = ""
	reaction["Performance_Data"]["Mass_Activity"]["number"] = 0.0

	reaction["Performance_Data"]["Conversion"] = dict()
	reaction["Performance_Data"]["Conversion"]["unit"] = ""
	reaction["Performance_Data"]["Conversion"]["number"] = 0.0

	reaction["Performance_Data"]["Selectivity"] = dict()
	reaction["Performance_Data"]["Selectivity"]["unit"] = ""
	reaction["Performance_Data"]["Selectivity"]["number"] = 0.0

	reaction["Performance_Data"]["Faradaic_Efficiency"] = dict()
	reaction["Performance_Data"]["Faradaic_Efficiency"]["unit"] = ""
	reaction["Performance_Data"]["Faradaic_Efficiency"]["number"] = 0.0

	reaction["Performance_Data"]["Time_On_Stream"] = dict()
	reaction["Performance_Data"]["Time_On_Stream"]["unit"] = ""
	reaction["Performance_Data"]["Time_On_Stream"]["number"] = 0.0

	reaction["Performance_Data"]["Recyclability"] = dict()
	reaction["Performance_Data"]["Recyclability"]["unit"] = ""
	reaction["Performance_Data"]["Recyclability"]["number"] = 0.0

	reaction["Performance_Data"]["Gas_Adsorption_Isotherm"] = dict()
	reaction["Performance_Data"]["Gas_Adsorption_Isotherm"]["unit"] = ""
	reaction["Performance_Data"]["Gas_Adsorption_Isotherm"]["number"] = 0.0

	reaction["Performance_Test_Raw_Data"] = dict()
	reaction["Performance_Test_Raw_Data"]["Conversion_Graph"] = ""
	reaction["Performance_Test_Raw_Data"]["FTIR_Graph"] = ""
	reaction["Performance_Test_Raw_Data"]["Raman_Graph"] = ""
	reaction["Performance_Test_Raw_Data"]["UV_VIS_Spectra_Graph"] = ""
	reaction["Performance_Test_Raw_Data"]["Degradation_Curve_Graph"] = ""
	reaction["Performance_Test_Raw_Data"]["Reaction_Kinetics_Plot_Graph"] = ""
	reaction["Performance_Test_Raw_Data"]["Recycle_Graph"] = ""
	reaction["Performance_Test_Raw_Data"]["Activity_Graph"] = ""
	reaction["Performance_Test_Raw_Data"]["Selectivity_Graph"] = ""
#	temp["Reaction"].append(reaction)
	temp["userId"] = "KIST"

	for i in range(len(json_list)):
		if material_list == []:
			material_list.append(json_list[i]['Material'])
		elif json_list[i]['Material'] not in material_list:
			material_list.append(json_list[i]['Material'])

	for i in range(len(material_list)):
		initial_json = copy.deepcopy(temp)
		initial_json["_id"] = url_text
		initial_json["docid"] = url_text
		initial_json["catalyst"] = material_list[i]
		data_store = 0
		sub_data = dict()
		data1 = dict()
		for	j in range(len(json_list)):
			if material_list[i] == json_list[j]['Material']:
				for k in range(len(Properties)):
					prop_regex = re.compile(Regex[k], re.I)
					if prop_regex.search(json_list[j]['Property']):
						data_store = 1
						#Store Each data
						if Properties[k] == "Composition":
							data = dict()
							data['Element'] = json_list[j]['Property']
							data['Atomic_Ratio'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Catalyst_Composition"].append(data)
							break

						elif Properties[k] == "Promoter":
							data = dict()
							data['Element'] = json_list[j]['Property']
							data['Atomic_Ratio'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Promoter"].append(data)
							break

						elif Properties[k] == "Surface area":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Measured_Value'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Specific_Surface_Area"].append(data)
							break

						elif Properties[k] == "Active site area":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Measured_Value'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Active_Site_Area_By_Chemisorption"].append(data)
							break

						elif Properties[k] == "Porosity":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Measured_Value'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Porosity"].append(data)
							break

						elif Properties[k] == "Pore volume":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Measured_Value'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Total_Pore_Volume"].append(data)
							break

						elif Properties[k] == "Acidity":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Bronsted_Acidity'] = 0.0
							data['Lewis_Acidity'] = 0.0
							data['Total_Acidity'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Acidity"].append(data)
							break

						elif Properties[k] == "Basicity":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Bronsted_Acidity'] = 0.0
							data['Lewis_Acidity'] = 0.0
							data['Total_Acidity'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Basicity"].append(data)
							break

						elif Properties[k] == "Adsorption energy":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Reactant'] = json_list[j]['Caption']
							data['Calculated_Value'] = 0.0
							data['Measured_Value'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Adsorption_Energy"].append(data)
							break

						elif Properties[k] == "Diffusivity":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Calculated_Value'] = 0.0
							data['Measured_Value'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Diffusivity_On_Support"].append(data)
							break

						elif Properties[k] == "Optical band gap":
							data = dict()
							data['Condition'] = json_list[j]['Property'] +'\t'+ json_list[j]['Footnote']
							data['Calculated_Value'] = 0.0
							data['Measured_Value'] = json_list[j]['Value']
							initial_json["Characterization_Data"]["Optial_Band_Gap"].append(data)
							break

##### Write reaction / method / etc..
						else:
							if sub_data == {}:
								data1 = copy.deepcopy(reaction)
								sub_data = copy.deepcopy(method)
								sub_data["Reactants"] = json_list[j]['Material']
								sub_data["Products"] = ""
								sub_data["Reactant_Datagram"] = json_list[j]["Caption"]

								data1["Performance_Test_Method"].append(sub_data)
								if Properties[k] == "Conversion":
									data1["Performance_Data"]["Conversion"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Conversion"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Yield":
									data1["Performance_Data"]["Yield"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Yield"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Productivity":
									data1["Performance_Data"]["Productivity_Yield"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Productivity_Yield"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Selectivity":
									data1["Performance_Data"]["Selectivity"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Selectivity"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Faradaic efficiency":
									data1["Performance_Data"]["Faradaic_Efficiency"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Faradaic_Efficiency"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Turnover frequency":
									data1["Performance_Data"]["TurnOver_Frequency"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["TurnOver_Frequency"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Rate constant":
									data1["Performance_Data"]["Rate_Constant"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Rate_Constant"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Recyclability":
									data1["Performance_Data"]["Recyclability"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Recyclability"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Activity":
									data1["Performance_Data"]["Specific_Activity"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Specific_Activity"]["number"] = json_list[j]["Value"]
									break


							elif sub_data["Reactant_Datagram"] == json_list[j]["Caption"]:
								if Properties[k] == "Conversion":
									if data1["Performance_Data"]["Conversion"]["unit"] == "":
										data1["Performance_Data"]["Conversion"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["Conversion"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["Conversion"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["Conversion"]["number"] += ", " + json_list[j]["Value"]
										break

								elif Properties[k] == "Yield":
									if data1["Performance_Data"]["Yield"]["unit"] == "":
										data1["Performance_Data"]["Yield"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["Yield"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["Yield"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["Yield"]["number"] += ", " + json_list[j]["Value"]
										break

								elif Properties[k] == "Productivity":
									if data1["Performance_Data"]["Productivity_Yield"]["unit"] == "":
										data1["Performance_Data"]["Productivity_Yield"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["Productivity_Yield"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["Productivity_Yield"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["Productivity_Yield"]["number"] += ", " + json_list[j]["Value"]
										break

								elif Properties[k] == "Selectivity":
									if data1["Performance_Data"]["Selectivity"]["unit"] == "":
										data1["Performance_Data"]["Selectivity"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["Selectivity"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["Selectivity"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["Selectivity"]["number"] += ", " + json_list[j]["Value"]
										break

								elif Properties[k] == "Faradaic efficiency":
									if data1["Performance_Data"]["Faradaic_Efficiency"]["unit"] == "":
										data1["Performance_Data"]["Faradaic_Efficiency"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["Faradaic_Efficiency"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["Faradaic_Efficiency"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["Faradaic_Efficiency"]["number"] += ", " + json_list[j]["Value"]
										break

								elif Properties[k] == "Turnover frequency":
									if data1["Performance_Data"]["TurnOver_Frequency"]["unit"] == "":
										data1["Performance_Data"]["TurnOver_Frequency"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["TurnOver_Frequency"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["TurnOver_Frequency"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["TurnOver_Frequency"]["number"] += ", " + json_list[j]["Value"]
										break

								elif Properties[k] == "Rate constant":
									if data1["Performance_Data"]["Rate_Constant"]["unit"] == "":
										data1["Performance_Data"]["Rate_Constant"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["Rate_Constant"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["Rate_Constant"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["Rate_Constant"]["number"] += ", " + json_list[j]["Value"]
										break

								elif Properties[k] == "Recyclability":
									if data1["Performance_Data"]["Recyclability"]["unit"] == "":
										data1["Performance_Data"]["Recyclability"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["Recyclability"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["Recyclability"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["Recyclability"]["number"] += ", " + json_list[j]["Value"]
										break

								elif Properties[k] == "Activity":
									if data1["Performance_Data"]["Specific_Activity"]["unit"] == "":
										data1["Performance_Data"]["Specific_Activity"]["unit"] = json_list[j]["Property"]
										data1["Performance_Data"]["Specific_Activity"]["number"] = json_list[j]["Value"]
										break
									else:
										data1["Performance_Data"]["Specific_Activity"]["unit"] += ", " + json_list[j]["Property"]
										data1["Performance_Data"]["Specific_Activity"]["number"] += ", " + json_list[j]["Value"]
										break

							elif sub_data["Reactant_Datagram"] != json_list[j]["Caption"]:
								initial_json["Reaction"].append(data1)
								data1 = copy.deepcopy(reaction)
								sub_data = copy.deepcopy(method)
								sub_data["Reactants"] = json_list[j]['Material']
								sub_data["Products"] = ""
								sub_data["Reactant_Datagram"] = json_list[j]["Caption"]

								data1["Performance_Test_Method"].append(sub_data)

								if Properties[k] == "Conversion":
									data1["Performance_Data"]["Conversion"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Conversion"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Yield":
									data1["Performance_Data"]["Yield"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Yield"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Productivity":
									data1["Performance_Data"]["Productivity_Yield"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Productivity_Yield"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Selectivity":
									data1["Performance_Data"]["Selectivity"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Selectivity"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Faradaic efficiency":
									data1["Performance_Data"]["Faradaic_Efficiency"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Faradaic_Efficiency"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Turnover frequency":
									data1["Performance_Data"]["TurnOver_Frequency"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["TurnOver_Frequency"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Rate constant":
									data1["Performance_Data"]["Rate_Constant"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Rate_Constant"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Recyclability":
									data1["Performance_Data"]["Recyclability"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Recyclability"]["number"] = json_list[j]["Value"]
									break

								elif Properties[k] == "Activity":
									data1["Performance_Data"]["Specific_Activity"]["unit"] = json_list[j]["Property"]
									data1["Performance_Data"]["Specific_Activity"]["number"] = json_list[j]["Value"]
									break

			else:
				continue
		initial_json["Reaction"].append(data1)
		if data_store == 1:
			JSON.append(initial_json)

	print (len(material_list),'\n',material_list)
	return JSON



# OUTPUT standardization to table
def transform(json_list):
	Properties = ['Temperature','Precursor Ratio','Synthesis Time','Particle Size','Surface Area','Cycle Retention Stability','Voltage','Conductivity','Diffusion Coefficient','Capacity','Band Gap','Activation Energy']
	Regex = ['[tT]emp','[Pp]recursor','[Tt]ime','[Pp]article [Ss]ize|Size','[Ss]urface area|SA','[Cc]ycle [Rr]etention|[Rr]etention','Voltage|\sV\s','[Cc]onducti','[Dd]iffus','[Cc]apacit','[Bb]and [Gg]ap','[Aa]ctivation [Ee]nergy|E[Aa]']
	Fulltext_regex = ['[Tt]emperature|[Tt]emp','[Pp]recursor [Rr]atio','[Ss]ynthesis [Tt]ime','[Pp]article [Ss]ize|[Ss]ize','[Ss]urface [Aa]rea','[Cc]ylce [Rr]etention [Ss]tability','[Vv]oltage','[Cc]onductivity','[Dd]iffusion [Cc]oefficient','[Cc]apatity|[Cc]apacitance','[Bb]and [Gg]ap','[Aa]ctivation [Ee]nergy']
	Tag = ['T','PR','ST','PS','SA','CRS','V','IC','DC','C','BG','AE']

	Excel = []
#	template = ['','','','','','','','','','','','','','','','','','','','','','','','',''] #Mat + condition[unit or prop raw data]/value * 12
	numcol = 2 * len(Properties) + 2 # Materials+Mat_description + Rawprop + Value
	for i in range(numcol):
		Excel.append([''])

	nowrow = 0
	for i in range(len(json_list)):
#		print (Excel)
		data_store = 0
		for j in range(len(Properties)):
			prop_regex = re.compile(Regex[j])
			fulltext_regex = re.compile(Fulltext_regex[j])
			if prop_regex.search(json_list[i]['Property']):
				if data_store == 0:
					if Excel[1][nowrow] == '':
						Excel[0][nowrow] = json_list[i]['simple_mat']
						Excel[1][nowrow] = json_list[i]['Material']
						Excel[2*j+2][nowrow] = json_list[i]['Property']
						Excel[2*j+3][nowrow] = json_list[i]['Value']
						data_store = 1
#						print ('case#1')
					elif Excel[1][nowrow] != '' and any(json_list[i]['Material'] in s for s in Excel[1][:nowrow+1]) == True:
						for k in range(nowrow+1):
							#print (json_list[i]['Material'], Excel[1][k])
							if json_list[i]['Material'] == Excel[1][k]:
								write = k
								break
						if Excel[2*j+3][write] == '':
							Excel[2*j+2][write] = json_list[i]['Property']
							Excel[2*j+3][write] = json_list[i]['Value']
							data_store = 1
#							print ('case#2')
						else:
							done = 0
							while done == 0:
								if write + 1 == len(Excel[1]):
									nowrow += 1
									done = 1
									break
								if Excel[1][write+1] == json_list[i]['Material']:
									if Excel[2*j+3][write+1] == '':
										Excel[2*j+2][write+1] = json_list[i]['Property']
										Excel[2*j+3][write+1] = json_list[i]['Value']
										data_store = 1
#										print ('case#3')
										break
									else:
										write += 1
								else:
									done = 1
							if done == 1:
								for l in range(len(Excel)):
									Excel[l].insert(write + 1,'')
								Excel[0][write+1] = json_list[i]['simple_mat']
								Excel[1][write+1] = json_list[i]['Material']
								Excel[2*j+2][write+1] = json_list[i]['Property']
								Excel[2*j+3][write+1] = json_list[i]['Value']
#								print ('case#4')
								data_store = 1
					elif Excel[1][nowrow] != '' and any(json_list[i]['Material'] in s for s in Excel[1][:nowrow+1]) == False:
						for k in range(len(Excel)):
							Excel[k].append('')
						Excel[0][nowrow+1] = json_list[i]['simple_mat']
						Excel[1][nowrow+1] = json_list[i]['Material']
						Excel[2*j+2][nowrow+1] = json_list[i]['Property']
						Excel[2*j+3][nowrow+1] = json_list[i]['Value']
						data_store = 1
#						print ('case#5')
						nowrow += 1
	return Excel

def metadata(fff): # Extract Author/Title/etc like metadata from Elsevier.
	doi = ''
	title = ''
	journal = ''
	date = ''
	Author_list = []
	i = fff.find('coredata')

	doi = i.find('prism:doi').text
	title = i.find('dc:title').text
	journal = i.find('prism:publicationname').text
	date = i.find('prism:coverdate').text
	for j in i.find_all('dc:creator'):
		Author_list.append(j.text)

	return [doi, title, journal, date, Author_list]



def extract_table_xml(filename, url_text = None, show_data = True, write_rawfile = True, write_datafile = True, output_filename = None, reader = 'elsevier'):
	"""Extract data from table
	---------------------------------
	filename : (str) name of file
	url_text : (str) url of data (reference)
	show_data : (bool) if True, print data
	write_rawfile : (bool) if True, write .raw file
	write_datafile : (bool) if True, write .data file
	output_filename : (str) name of output file (when write_rawfile is True)
	---------------------------------
	output : json_list
	
	"""
	
	### 1.Open files
	#print (filename+'\n')
	f = open(filename, 'rb')
	ff = open(filename, encoding='UTF-8')
	fff = BeautifulSoup(ff, 'lxml')
	
	if not output_filename:
		output_filename = filename
	filename_reduced = str(output_filename).replace(".xml","")
		
	if write_rawfile:
		out1 = open(filename_reduced+".raw","w", encoding = 'UTF-8')
	if write_datafile:
		out5 = open(filename_reduced+".data","w", encoding = 'UTF-8')


	# Write metadata in .raw file
	if write_rawfile:
		META = metadata(fff)
		out1.write('DOI'+'\t'+META[0]+'\n')
		out1.write('Title'+'\t'+META[1]+'\n')
		out1.write('Journal'+'\t'+META[2]+'\n')
		out1.write('Publication_date'+'\t'+META[3]+'\n')
		text = ''
		for i in range(len(META[4])):
			text += META[4][i] + '\t'
		out1.write('Author'+'\t'+text[:-1]+'\n')
		out1.write('\n')

	url_text = filename

	ff.close()

	Total_DATA = []
	Sentences = []
	#Tokens = []
	Tabledata = []
	Abbreviations = []
	elements = []
	Text_ori = ''

	if reader == "elsevier":
		for i in fff.find_all("ce:para"):
			for hyperlink in i.find_all(["ce:cross-refs", "ce:cross-ref", "ce:footnote"]):
				hyperlink.extract()

			text = i.text
			text = text.replace("\n", "")
			Text_ori += text+'\n\n'
		doc = Document(Text_ori)
	else:
		doc = Document.from_file(f) #can select available reader using 'readers' option

	### 2.Tokenize & Abbreviations

	Para = doc.elements
	count_para=0
	count_table=0
	for i in range(len(Para)):
		if isinstance(Para[i], Paragraph):
			count_para += 1
			Sentences.append(Para[i].sentences)
			if Para[i].abbreviation_definitions != []:
				Abbreviations.append(Para[i].abbreviation_definitions)
	temp_list = []
	for i in range(len(Sentences)):
		temp_list = temp_list + Sentences[i]
	Sentences = temp_list
	for i in range(len(Sentences)):
		Sentences[i] = Sentences[i].text
	#print (Sentences)
	### 3.Identify chemical names

	Chemicals = doc.cems
	#print (Chemicals)
	chemical_list = []
	for i in range(len(Chemicals)):
		chemical_list.append(clean_text(Chemicals[i].text))

	chemical_list = removeDuplicates(chemical_list)

	#print (chemical_list)
	### 4.Identify Abbreviations
	temp_list = []
	# Make all Abbreviations list
	for i in range(len(Abbreviations)):
		temp_list = temp_list + Abbreviations[i]
	Abbreviations = temp_list


	for i in reversed(range(len(Abbreviations))): # Delete Abbreviations when the Abbreviations is lower case *** NUMBER INCLUDED CASE (to be modified)
		if tuple_sum(Abbreviations[i][0]).islower():
			del Abbreviations[i]


	#print ('<Abbreviations>\n')

	for i in range(len(Abbreviations)):
		if Abbreviations[i][2] == 'CM':
			if write_rawfile:
#				print (tuple_sum(Abbreviations[i][0])+ ': ' + tuple_sum(Abbreviations[i][1]))
				out1.write(tuple_sum(Abbreviations[i][0])+ ': ' + tuple_sum(Abbreviations[i][1])+'\n')

	for i in range(len(Abbreviations)):
		if Abbreviations[i][2] == 'CM' and tuple_sum(Abbreviations[i][0]) not in chemical_list:
			chemical_list.append(tuple_sum(Abbreviations[i][0]))
		if Abbreviations[i][2] != 'CM' and tuple_sum(Abbreviations[i][0]) in chemical_list:
			chemical_list.remove(tuple_sum(Abbreviations[i][0]))

	#print (len(chemical_list))
	#print (chemical_list)
	### 5. Table Data Control
	num_data_table = 0
	num_each_prop = [0,0,0,0,0,0,0,0,0,0,0,0]
	
	if write_rawfile:
		out1.write('\n\n\n')
	tables = fff.find_all("ce:table")
	Caption_list = []
	json_list = []
	for table in tables:
	# Find Captions and Footnotes
		caption = ''
		Footnote_list = []

		try: # Try to extract caption
			caption += table.find("ce:label").text
			caption += ". "	
			caption += table.find("ce:caption").text
		except:
			pass

		try: # Try to extract footnote
			for footnote in table.find_all("ce:legend"):
				Footnote_list.append(footnote.text.replace("\n",""))
			for footnote in table.find_all("ce:table-footnote"):
				Footnote_list.append([footnote.find("ce:label").text, footnote.find("ce:note-para").text.replace("\n","")])
		except:
			pass

		th_row = 0
		if table != None:
			tgroups = table.find_all("tgroup")
			tgroupnum = 0
			for tgroup in tgroups:
				data = []
				temp_data = []
				tgroupnum += 1
				colmax = int(tgroup.attrs.get('cols'))
				table_head  = tgroup.thead
				head_crit = 0
				if table_head != None:
					head_crit = 1
					rows = table_head.find_all('row')
					rownum = 0
					for rep in range(colmax):
						temp_data.append([])
					for row in rows:
						rownum += 1
						data.append([])
						for rep in range(colmax):
							data[rownum-1].append([])
						cols = row.find_all('entry')
						colnum = 0
						now_cols = 0
						for col in cols:
							now_cols += 1
							colnum += 1
							if temp_data[colnum-1] != []:
								data[rownum-1][colnum-1].append(temp_data[colnum-1].pop(0))
								continue
							if colnum > colmax:
								print ("Error:Wierd_Table")
							namest = 0
							nameend = 0
							morerows = 0
							try:
								morerows = int(col.attrs.get('morerows'))
							except:
								pass
							try:	
								namest = int(col.attrs.get('namest').replace("col",""))
								nameend = int(col.attrs.get('nameend').replace("col",""))
							except:
								pass

							if morerows != 0:
								if namest == 0 and nameend == 0:
									for more in range(morerows):
										text = col.text.strip()
										text = clean_text(text)
										temp_data[colnum-1].append(text)
								else:
									for more in range(morerows):
										for rep in range(namest-1,nameend):
											text = col.text.strip()
											text = clean_text(text)
											temp_data[rep].append(text)
									

							if namest == 0 and nameend == 0:
								#text pretreatment
								text = col.text.strip()
								text = clean_text(text)
								if text != '':
									data[rownum-1][colnum-1].append(text)
							else:
								colnum += (nameend - namest)
								for rep in range(namest-1,nameend):
									text = col.text.strip()
									text = clean_text(text)
									data[rownum-1][rep].append(text)

							if now_cols == len(cols) and colnum < colmax:
								colnum += 1
								for i in range(colnum-1,colmax):
									try:
										data[rownum-1][i].append(temp_data[i].pop(0))
									except:
										pass



					th_row = rownum

#				else:
#					print ("Error:No_thead_table")
#					continue:


				table_body = tgroup.tbody
				if table_body != None:
					morerows = 0
					rows = table_body.find_all('row')
					head_row_num = len(data)
					if head_row_num == 0:
						head_row_num = 1
					rownum = len(data)
					for row in rows:
						rownum += 1
						data.append([])
						for rep in range(colmax):
							data[rownum-1].append([])
						cols = row.find_all(['entry'])
						colnum = 0
						now_cols = 0
						for col in cols:
							now_cols += 1
							colnum += 1
							#print (colnum, colmax, temp_data[colnum-1])
							if temp_data[colnum-1] != []:
								data[rownum-1][colnum-1].append(temp_data[colnum-1].pop(0))
								continue

							if colnum > colmax:
								print ("Error:Wierd_Table")
							namest = 0
							nameend = 0
							morerows = 0
							try:
								morerows = int(col.attrs.get('morerows'))
							except:
								pass
							try:
								namest = int(col.attrs.get('namest').replace("col",""))
								nameend = int(col.attrs.get('nameend').replace("col",""))
							except:
								pass

							if morerows != 0:
								if namest == 0 and nameend == 0:
									for more in range(morerows):
										text = col.text.strip()
										text = clean_text(text)
										temp_data[colnum-1].append(text)
								else:
									for more in range(morerows):
										for rep in range(namest-1,nameend):
											text = col.text.strip()
											text = clean_text(text)
											temp_data[rep].append(text)
							#print (temp_data)
							if namest == 0 and nameend == 0:
								#text pretreatment
								text = col.text.strip()
								text = clean_text(text)
								if text != '':
									data[rownum-1][colnum-1].append(text)
							else:
								colnum += (nameend - namest)
								for rep in range(namest-1,nameend):
									text = col.text.strip()
									text = clean_text(text)
									data[rownum-1][rep].append(text)
							if now_cols == len(cols) and colnum < colmax:
								colnum += 1
								for i in range(colnum-1,colmax):
									try:
										data[rownum-1][i].append(temp_data[i].pop(0))
									except:
										pass
				else:
					continue


				for i in range(len(data)):
					for j in range(len(data[i])):
						if data[i][j] == []:
							data[i][j].append('')
#					print (data[i])


			# Identify the data part of table
				oldChars = '(){}[]<>~%±×.,-:/V―C−'
				newChars = '                     '
				if th_row == 0:
					for j in range(len(data)):
						if j > 2:
							break
						th_crit = 1
						for i in range(len(data[j])):
							text = data[j][i][0]
							if is_digit(text.translate({ ord(x): y for (x, y) in zip(oldChars, newChars) }).replace(" ", "")) == True:
								th_crit = 0
						if th_crit == 1:
							th_row += 1
	
				cat_row = 0
				for j in range(len(data[0])):
					if j > 2: # prevent considering last reference part as Catalyst column
						break
					th_crit = 1
					for i in range(len(data) - th_row):
						text = data[i+th_row][j][0]
						if is_digit(text.translate({ ord(x): y for (x, y) in zip(oldChars, newChars) }).replace(" ", "")) == True:
							th_crit = 0
						#print (i+th_row, j, text, text.translate({ ord(x): y for (x, y) in zip(oldChars, newChars) }).replace(" ", ""), th_crit)
					if th_crit == 1:
						cat_row = j+1
	

				# Prettify rows for cat_rows
				for i in range(len(data) - th_row):
					for j in range(cat_row):
						if (i != 0) and (data[i+th_row][j][0] == ''):
							data[i+th_row][j].remove('')
							data[i+th_row][j].append(data[i+th_row-1][j][0])
	
				#print (th_row, cat_row)
	
	
			#Strategy 2
				left_table = 0
				crit = 1
				
#				print ("<left_percentage>")	
				#calculate rows and columns cems percentage
				num_rowword = (len(data) - th_row) * cat_row
				num_colword = (len(data[0]) - cat_row) * th_row
				row_percentage = 0.0
				for i in range(th_row,len(data)):
					for j in range(cat_row):
			#			print (data[i][j][0])
						if data[i][j][0] != '':
							row_percentage += chem_percentage(data[i][j][0],chemical_list)/num_rowword
#							print (data[i][j][0], ischemical(data[i][j][0],chemical_list), row_percentage)


#				print ("<top_percentage>")
				col_percentage = 0.0
				for i in range(th_row):
					for j in range(cat_row,len(data[i])):
		#				print (data[i][j][0])
						if data[i][j][0] != '':
							col_percentage += chem_percentage(data[i][j][0],chemical_list)/num_colword
#							print (data[i][j][0], ischemical(data[i][j][0],chemical_list), col_percentage)
				row_percentage = round(row_percentage,2)
				col_percentage = round(col_percentage,2)
	
			# If there is catalyst word, probability of feature top table goes up!
#				print (row_percentage, col_percentage)
				added = 0
				for i in range(th_row):
					for j in range(cat_row):
						if added == 0:
#							print (data[i][j][0])
							if data[i][j][0].find('atalyst') != -1 or data[i][j][0].find('ample')!= -1 or data[i][j][0].find('aterial')!= -1:
								row_percentage += 0.5
								added = 1
							if data[i][j][0].find('roperty') != -1:
								row_percentage -= 0.5
								added = 1
	
				if row_percentage > col_percentage:
					left_table = 0
				elif col_percentage > row_percentage:
					left_table = 1
				else:# just output or consider as left_table (in general left table)
					left_table = 0
	
				need_to_print_original_table = 0
				# RULE1: confused left / top header
				#	if row_percentage == col_percentage:
				#		need_to_print_original_table = 1
#				print (row_percentage, col_percentage, left_table)
	
	
				export_data = []
				SIM_CAT = []
				# General table data extraction logic
				if left_table == 0:
					for i in range(len(data) - th_row):
						for j in range(len(data[i]) - cat_row):
							dataline = ''
							if data[i+th_row][j+cat_row][0] == '':
								continue
							cat_text = ''
							sim_cat = ''
							for k in range(cat_row):
								entry_line = 0
								for l in range(th_row):
									if data[l][k][0] == '':
										continue
									elif (l != 0) and (data[l][k][0] == data[l-1][k][0]):
										continue
									else:
										if data[l][k][0].find('ntry') != -1 or data[l][k][0].find('Run') != -1 or data[l][k][0].find('no.') != -1 or data[l][k][0].find('No.') != -1 or data[l][k][0] == "#":
											entry_line = 1
										else:
											cat_text += ' '+data[l][k][0]
								if entry_line != 1:
									cat_text += ' '+data[i+th_row][k][0]
									if sim_cat == '' and ischemical(data[i+th_row][k][0],chemical_list):
										sim_cat = data[i+th_row][k][0]
			#						print (cat_text, sim_cat)
		
			#					print (k, l, data[l][k][0], entry_line, cat_text)
			#				sim_cat = data[i+th_row][k][0]
							cat_text = cat_text.strip()
							if cat_text == '':
								cat_text = 'No_Catalyst_Info'
								need_to_print_original_table = 1
			#					print ("here1")
							feature_text = ''
							for k in range(th_row):
								if data[k][j+cat_row][0] == '':
									continue
								elif (k != 0) and (data[k][j+cat_row][0] == data[k-1][j+cat_row][0]):
									continue
								else:
									feature_text += ' '+data[k][j+cat_row][0]
							feature_text = feature_text.strip()
							if feature_text == '':
								feature_text = 'No_Feature_Info'
								need_to_print_original_table = 1
			#					print ("here2")
							if cat_text.find(data[i+th_row][j+cat_row][0]) == -1 and feature_text.find(data[i+th_row][j+cat_row][0]) == -1:
								if len(feature_text) < 5 or cat_text.find(feature_text) == -1:
									dataline = cat_text + ' ★ ' + feature_text + ' ★ ' + data[i+th_row][j+cat_row][0]
									export_data.append(dataline)
									SIM_CAT.append(sim_cat)
				else: # feature left table case
			#		print ("here")
					for j in range(len(data[0]) - cat_row):
						for i in range(len(data) - th_row):
							if data[i+th_row][j+cat_row][0] == '':
								continue

							feature_text = ''
							for l in range(th_row):
								for k in range(cat_row):
									entry_line = 0
									if data[l][k][0] == '':
										continue
									elif (k != 0) and (data[l][k][0] == data[l][k-1][0]):
										continue
									else:
										if data[l][k][0].find('ntry') != -1 or data[l][k][0].find('Run') != -1 or data[l][k][0].find('no.') != -1 or data[l][k][0].find('No.') != -1  or data[l][k][0] == "#" or data[l][k][0].find('Ref.') != -1:
											entry_line = 1
										else:
											feature_text += ' '+data[l][k][0]
									if entry_line != 1:
										feature_text += ' '+data[i+th_row][k][0]
							feature_text = feature_text.strip()

							if feature_text == '':
								feature_text = 'No_Feature_Info'
								need_to_print_original_table = 1
							#print (feature_text)

							sim_cat = ''
							cat_text = ''
							for k in range(th_row):
								if data[k][j+cat_row][0] == '':
									continue
								elif (k != 0) and (data[k][j+cat_row][0] == data[k-1][j+cat_row][0]):
									continue
								else:
									cat_text += ' '+data[k][j+cat_row][0]
									if sim_cat == '' and ischemical(data[l][j+cat_row][0],chemical_list):
										sim_cat = data[i+th_row][k][0]
							cat_text = cat_text.strip()
							
							if cat_text == '':
								cat_text = 'No_Catalyst_Info'
								need_to_print_original_table = 1
					#			print ("here4")
							if cat_text.find(data[i+th_row][j+cat_row][0]) == -1 and feature_text.find(data[i+th_row][j+cat_row][0]) == -1:
								if len(feature_text) < 5 or cat_text.find(feature_text) == -1:
									dataline = cat_text + ' ★ ' + feature_text + ' ★ ' + data[i+th_row][j+cat_row][0]
									export_data.append(dataline)
									SIM_CAT.append(sim_cat)
				export_data,Num = statistics(export_data)
		
				# Print Data
				data1 = []
				data2 = []
				if export_data != []:
					num_data_table += 1
					out = 0
					for j in range(len(export_data)-1):
						for k in range(j+1,len(export_data)):
							if out == 0:
								data1 = export_data[j].split(' ★ ')
								data2 = export_data[k].split(' ★ ')
			#					print (data1)
			#					print (data2)
			# RULE2: material same value different
								if data1[0] == data2[0] and data1[1] == data2[1] and data1[2] != data2[2]:
			#						need_to_print_original_table = 1
									out = 1
		
				if export_data != [] and need_to_print_original_table == 0:
		
				# Print Caption
					caption_crit = 0
					try:
						if caption != None and any(caption in s for s in Caption_list) == False:
							caption_crit = 1
							Caption_list.append(clean_text(caption))
					except:
						pass
		
	
			#		for j in range(len(export_data)):
			#			out1.write(export_data[j]+'\n')
			#		out1.write('\n')
		
					# Print Footnote
					footnote_crit = 0
					try:
						if Footnote_list != []:
							footnote_crit = 1
							footnote_long = ''
							for j in range(len(Footnote_list)):
								if type(Footnote_list[j]) == list:
									temp = ''
									for k in range(len(Footnote_list[j])):
										temp += Footnote_list[j][k]
										if k < len(Footnote_list[j]) - 1:
											temp += ':'
									footnote_long += temp
									footnote_long += '	'
								elif type(Footnote_list[j]) == str:
									footnote_long += Footnote_list[j]
									footnote_long += '	'
					except:
						pass
		
	
					# Store as python dict format
					json_name = ['Caption','simple_mat','Material','Property','Value','Footnote','Reference']
		
					for j in range(len(export_data)):
						if write_datafile:
							out5.write(export_data[j]+"\n")
						dict_tmp = {}
						json_value = []
						if caption_crit == 1:
							json_value.append(clean_text(caption))
						else:
							json_value.append('')
						json_value.append(SIM_CAT[j])
						json_value.append(export_data[j].split(" ★ ")[0])
						json_value.append(export_data[j].split(" ★ ")[1])
						json_value.append(export_data[j].split(" ★ ")[2])
						if footnote_crit == 1:
							json_value.append(footnote_long.strip())
						else:
							json_value.append('')
						json_value.append(url_text)
		
						for l,k in enumerate(json_name):
							val = json_value[l]
							dict_tmp[k] = val
						json_list.append(dict_tmp)
		
				if export_data != []:
		
				# Print Caption
					try:
						if write_rawfile:
							out1.write(Caption_list[-1])
							out1.write('\n\n')
					except:
						pass
	
	
					for i in range(len(data)):
						text = ''
						for j in range(len(data[i])):
							text += data[i][j][0] + '\t'
						text = text[:-1]
						if write_rawfile:
							out1.write(text+'\n')
					if write_rawfile:
						out1.write('\n')
		
		
				# Print Footnote
					try:
						if Footnote_list != []:
							for j in range(len(Footnote_list)):
								if write_rawfile:
									if type(Footnote_list[j]) == str:
										out1.write(Footnote_list[j])
									elif type(Footnote_list[j]) == list:
										temp = ''
										for k in range(len(Footnote_list[j])):
											temp += Footnote_list[j][k]
											if k < len(Footnote_list[j]) - 1:
												temp += ':'
										out1.write(temp+'\n')
	
					except:
						pass
					if write_rawfile:
						out1.write('\n\n\n')
		
		
		
#				for i in range(len(export_data)):
#					print (export_data[i])
				for i in range(len(Num)):
					num_each_prop[i] += Num[i]
	if show_data:
		print ("\n")
		print ("Number_of_total_table:", num_data_table)
		print ("\n")
		print("<Number_of_each_properties>")
		print("\n")
		
		Property_list = ['Temperature','Precursor Ratio','Synthesis Time','Particle Size','Surface Area','Cycle Retention Stability','Voltage','Conductivity','Diffusion Coefficient','Capacity','Band Gap','Activation Energy']
		
		for i in range(len(Property_list)):
			print (Property_list[i],":",num_each_prop[i])
	
					
	if write_rawfile:
		out1.close()
	if write_datafile:
		out5.close()
				
	return json_list
		
		
def write_file(json_list, filename, url_text = None):
	"""write file as json, excel, json2
	------------------------------------------------------------
	json_list : (json) output of func (extract_data)
	filename : (str) name of output file
	url_text : (str) name of url (default : None, same as filename)
	----------------------------------------------------------------
	"""
	
	filename_reduced = re.sub(r"[.](html|xml|pdf)", "", filename)
	out2 = open(filename_reduced+".json","w", encoding = 'UTF-8')
	out3 = open(filename_reduced+".excel","w", encoding = 'UTF-8')
	out4 = open(filename_reduced+".json2","w", encoding = 'UTF-8')
	
	if not url_text:
		url_text = filename
	
	out4.write(json.dumps(json_list))
	out2.write(json.dumps(ast.literal_eval(json.dumps(transform_kist(json_list,url_text, return_count = True)[0]))))
	
	Excel = transform(json_list)
	for i in range(len(Excel)):
		text = ''
		for j in range(len(Excel[i])):
			text += Excel[i][j] + '\t'
		out3.write(text+'\n')
	
	out2.close()
	out3.close()
	out4.close()

if __name__ == '__main__':
	filename = input("Input file name: ")
	print (filename+'\n')
	extract_table_xml(filename)

