"""

26/08/2022
"""

import json

env = {}

def load_env(filename='env.json') -> dict:
    """Load environment variables. Default filename=\"env.json\""""
    
    with open(filename, 'r') as f:
        json_obj = json.load(f)
    
    for key in json_obj:
        env[key] = json_obj[key]
    
    return env


def get_env(env_var: str):
    """Retrieve the requested environment variable"""

    return env[env_var]