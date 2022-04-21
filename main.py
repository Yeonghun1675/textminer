from tqdm import tqdm
from pathlib import Path
import logging
import json

from extract_mof_ver2 import extract_paragraph_mof

def __get_logger(logname):
    __logger = logging.getLogger(logname)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    stream_handler = logging.FileHandler(logname)
    stream_handler.setFormatter(formatter)
    __logger.addHandler(stream_handler)
    __logger.setLevel(logging.DEBUG)
    return __logger

logger = __get_logger('log_mof.txt')


dir_file = '/storage2/dudgns1675/MOFdictionary/example/Elsevier_XML'
parser = 'elsevier_xml_parser'
suffix = 'xml'
out_dir = './output/mof_data'


file_list = list(Path(dir_file).glob(f'*.{suffix}'))
#file_list = [Path(dir_file)/'10.1016_j.micromeso.2013.07.019.xml']

out_dir = Path(out_dir)
for file in tqdm(file_list):
    try:
        data = extract_paragraph_mof(file, parser=parser)
        if data:
            logger.info(f'{file.stem} success')
            
            with open(out_dir/f'{file.stem}.json', 'w') as f:
                json.dump(data, f)
        else:
            logger.info(f'{file.stem} does not have data')
            
    except Exception as e:
        logger.info(f'{file.stem} failed : {e}')
