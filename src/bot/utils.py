import toml
import json

class config_file_reader:
    @staticmethod
    def read_json(config_file: str):
        with open(config_file, 'r') as file:
            config_data = json.load(file)
        return config_data

    @staticmethod
    def read_toml(config_file: str):
        with open(config_file, 'r') as file:
            config_data = toml.load(file)
        return config_data
    
    @staticmethod
    def read_configs(file_path:str)->dict|str:
        if file_path.endswith(".json"):
            configs = config_file_reader.read_json(file_path)
        else:
            configs = config_file_reader.read_toml(file_path)
        return configs