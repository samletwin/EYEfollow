import yaml
from pathlib import Path
from dataclasses import dataclass
from config_default import reading, test_config

read_data = None
test_config_data = None

@dataclass(frozen=True)
class grade_data:
    message: str
    questions: list[dict]

@dataclass(frozen=True)
class text_test_config:
    padding_hor_px: int
    padding_ver_px: int
    minimum_font_size: int
    line_spacing: int

def write_reading_config():
    with open('config/reading.yaml', 'w') as file:
            yaml.dump(yaml.safe_load(reading), file)

def write_test_config():
    global test_config_data
    with open('config/test_config.yaml', 'w') as file:
        test_config_data = yaml.safe_load(test_config)
        yaml.dump(test_config_data, file)

def load_config_files():
    global read_data, test_config_data
    # make config dir if it does not exist
    Path('config').mkdir(parents=True, exist_ok=True) 
    try:
        with open('config/reading.yaml', 'r') as file:
            read_data = yaml.safe_load(file)
            if read_data is None: # write default config
                write_reading_config() 
    except FileNotFoundError:
        write_reading_config()
    try:
        with open('config/test_config.yaml', 'r') as file:
            test_config_data = yaml.safe_load(file)
            if test_config_data is None: # write default config
                write_test_config()
    except FileNotFoundError:
        write_test_config()
        
    if 'test_params' in test_config_data:
        for test_name, test_data in test_config_data['test_params'].items():
            if 'Instruction' in test_data and isinstance(test_data['Instruction'], str):
                test_data['Instruction'] = test_data['Instruction'].replace(r'\n', '\n')

def get_data_output_path() -> str:
    return test_config_data['general_config']['data_output_path']

def get_grade_data(grade: int) -> grade_data: 
    key = f'grade_{grade}'
    grade_info = read_data['grades_text'].get(key, {})
    text = grade_info.get('message', None)
    if text is None:
        return None
    questions = [
        {"message": q['message'], "options": q['options'].split('/'), "answer": q['answer']}
        for q in grade_info.get('questions', {}).values()
    ]
    return grade_data(message=text, questions=questions)

def get_text_test_config() -> text_test_config:
    data = test_config_data['test_params']['Text_Reading']
    return text_test_config(
        padding_hor_px=data['Padding_Horizontal_Px'],
        padding_ver_px=data['Padding_Vertical_Px'],
        minimum_font_size=data['Minimum_Font_Size'],
        line_spacing=data['Line_Spacing']
    )

# TODO: should add error handling for incorrect config
def get_full_test_config():
    return test_config_data['test_params']

def get_ball_radius_px() -> int:
    return test_config_data['test_config']['ball_radius_px']