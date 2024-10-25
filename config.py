import yaml
from dataclasses import dataclass

read_data = None
test_config_data = None

@dataclass(frozen=True)
class grade_data:
    message: str
    questions: list[str]
    answers: list[str]

@dataclass(frozen=True)
class text_test_config:
    padding_hor_px: int
    padding_ver_px: int
    minimum_font_size: int


def load_config_files():
    global read_data, test_config_data
    with open('config/reading.yaml', 'r') as file:
        read_data = yaml.safe_load(file)
    with open('config/test_config.yaml', 'r') as file:
        test_config_data = yaml.safe_load(file)
        # Iterate over the test parameters and replace '\n' with actual newline characters
        if 'test_params' in test_config_data:
            for test_name, test_data in test_config_data['test_params'].items():
                if 'Instruction' in test_data and isinstance(test_data['Instruction'], str):
                    test_data['Instruction'] = test_data['Instruction'].replace(r'\n', '\n')

    
def get_data_output_path() -> str:
    return test_config_data['general_config']['data_output_path']

def get_grade_data(grade: int) -> grade_data: 
    key = f'grade_{grade}'
    grade_info = read_data['grades_text'].get(key, {})
    text = grade_info.get('message', f'Text for grade {grade} not found')
    questions = [q['message'] for q in grade_info.get('questions', {}).values()]
    answers = [q['answer'] for q in grade_info.get('questions', {}).values()]
    return grade_data(message=text, questions=questions, answers=answers)

def get_text_test_config() -> text_test_config:
    data = test_config_data['test_params']['Text_Reading']
    return text_test_config(
        padding_hor_px=data['Padding_Horizontal_Px'],
        padding_ver_px=data['Padding_Vertical_Px'],
        minimum_font_size=data['Minimum_Font_Size']
    )

# should add error handling for incorrect config
def get_full_test_config():
    return test_config_data['test_params']

def get_ball_radius_px() -> int:
    return test_config_data['test_config']['ball_radius_px']