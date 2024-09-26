import yaml
from dataclasses import dataclass

read_data = None
test_config_data = None

@dataclass(frozen=True)
class grade_data:
    message: str
    questions: list[str]

def load_config_files():
    global read_data, test_config_data
    with open('config/reading.yaml', 'r') as file:
        read_data = yaml.safe_load(file)
    with open('config/test_config.yaml', 'r') as file:
        test_config_data = yaml.safe_load(file)
    
def get_grade_data(grade: int) -> grade_data: 
    key = f'grade_{grade}'
    grade_info = read_data['grades_text'].get(key, {})
    text = grade_info.get('message', f'Text for grade {grade} not found')
    questions = list(grade_info.get('questions', {}).values())
    return grade_data(message=text, questions=questions)

    