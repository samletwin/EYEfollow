# config.py
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class GradeData:
    message: str
    questions: list[dict]

@dataclass
class TestParams:
    duration: float
    frequency: float
    instruction: str
    x_pos: float
    y_pos: float
    minimum_font_size: int
    padding_horizontal_px: int
    padding_vertical_px: int
    # Add other test-specific parameters as needed

class ConfigHandler:
    def __init__(self):
        self.config_path = "config/test_config.yaml"
        self.reading_path = "config/reading.yaml"
        self.default_config = {
            'general_config': {'data_output_path': './output'},
            'test_config': {
                'ball_radius_px': 12,
                'countdown_duration_s': 3,
                'draw_refresh_rate_ms': 5,
                'state_machine_cycle_ms': 100
            },
            'test_params': {}
        }
        self.grade_data = {}
        self.load_all_configs()

    def load_all_configs(self):
        # Load test configuration
        Path('config').mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
                self.config = {**self.default_config, **self.config}
        except FileNotFoundError:
            self.config = self.default_config
            self.save_config()

        # Load grade data
        try:
            with open(self.reading_path, 'r') as f:
                reading_config = yaml.safe_load(f)
                self._parse_grade_data(reading_config)
        except FileNotFoundError:
            raise RuntimeError("Missing reading configuration file")

    def _parse_grade_data(self, reading_config: Dict[str, Any]):
        for grade_key, grade_info in reading_config['grades_text'].items():
            questions = []
            for q in grade_info['questions'].values():
                questions.append({
                    "message": q['message'],
                    "options": q['options'].split('/'),
                    "answer": q['answer']
                })
            self.grade_data[grade_key] = GradeData(
                message=grade_info['message'],
                questions=questions
            )

    def get_grade_data(self, grade: int) -> GradeData:
        key = f'grade_{grade}'
        return self.grade_data.get(key)

    def get_all_test_params(self) -> Dict[str, TestParams]:
        return {
            test_name: TestParams(
                duration=params.get('Duration', None),
                frequency=params.get('Frequency', None),
                instruction=params.get('Instruction', None),
                x_pos=params.get('X_pos', None),
                y_pos=params.get('Y_pos', None),
                minimum_font_size=params.get('Minimum_Font_Size', None),
                padding_horizontal_px=params.get('Padding_Horizontal_Px', None),
                padding_vertical_px=params.get('Padding_Vertical_Px', None)
            )
            for test_name, params in self.config['test_params'].items()
        }

    def update_test_params(self, test_name: str, params: Dict[str, Any]):
        if test_name not in self.config['test_params']:
            self.config['test_params'][test_name] = {}
        self.config['test_params'][test_name].update(params)

    def save_config(self):
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f)

    # Existing getters
    def get_data_path(self) -> str:
        return self.config['general_config']['data_output_path']
    
    def get_ball_radius(self) -> int:
        return self.config['test_config']['ball_radius_px']

# Singleton instance
config_handler = ConfigHandler()