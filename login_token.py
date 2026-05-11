'''What do I want my tokens to-do
Tokens are a form of authentication 
users should only be allowed the permissions to perform their functions
'''


#   imports
from pydantic import validate_call
from dataclasses import dataclass, asdict, is_dataclass
from typing import Literal, Set

import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal, Set
from contextlib import contextmanager

from flask import Flask, render_template, request, redirect, url_for, flash

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

permission = Literal["access", "denied"]
action = Literal["execute", "read", "write"]

@dataclass
class User:
    user: str
    account_level: str
@dataclass
class Token:
    token: str
    permission: permission
    actions: Set[action]

#   Session
@dataclass
class Session:
    user: User
    token: Token
    cookies: list[str]

'''type checker ty from ruff'''
#   Variables
users = []
list_tokens = []
list_cookies = []
#   Dictionaries
user_dict = {}
token_dict = {}
cookie_dict = {}
#   Functions

'''code to access json files -->'''

def save_json_data(filepath: str, data): #  data: Dict[str, Any]
    """Save JSON data atomically"""
    tmp_path = Path(filepath + '.tmp')
    try:
        if is_dataclass(data) and not isinstance(data, type):
            data = asdict(data)
        with tmp_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(filepath)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

def select_json_file(directory: str) -> str:
    """Select JSON file interactively with validation"""
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    json_files = [f for f in directory.iterdir() if f.suffix.lower() == '.json']
    if not json_files:
        raise ValueError(f"No .json files found in: {directory}")

    print(f"\nAvailable JSON files in {directory}:")
    for i, f in enumerate(json_files, 1):
        print(f"  {i}. {f.name}")

    while True:
        try:
            choice = input(f"\nSelect file [1-{len(json_files)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(json_files):
                return str(json_files[idx].resolve())
            print("Invalid choice")
        except ValueError:
            print("Please enter a number")


def load_json_data(filepath: str, default: Dict[str, Any] = None, to_dataclass: bool = False) -> Dict[str, Any]:
    """Load JSON data with fallback
    - 'default': fallback dict if file is invalid
    - 'to_dataclass': rebuild session
    """
    filepath = Path(filepath)
    default = default or {}
    try:
        with filepath.open() as f:
            data = json.load(f)
# return data if isinstance(data, dict) else default
    except (json.JSONDecodeError, FileNotFoundError):
        return default.copy()
    if to_dataclass:
        try:
            user = User(**data["user"])
            token = Token(**data["token"])
            cookies = data.get("cookies", [])
            return Session(user=user, token=token, cookies=cookies)
        except (KeyError, TypeError):
            print('warning')
            return data
    return data


'''this is additional json code'''

def append_to_json(new_data, filename='home_page.json'):
    filepath = Path(filename)
    if is_dataclass(new_data):
        new_data = asdict(new_data)
    if not filepath.exists():
        with filepath.open('w') as f:
            json.dump({'items': [new_data]}, f, indent=4)
        return
    with filepath.open('r+') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {'items': []}
#     session = Session(
#     user=User(**data['user']),
#     token=Token(**data['token']),
#     cookies=data['cookies']
# )
        if not isinstance(data, dict) or 'items' not in data:
#     file_data['items'].append(new_data)
#     file.seek(0)
#     json.dump(file_data, file, indent=4)
#     file.truncate()
# else:
            raise ValueError(f'Expected "items" key in JSON {filename} structure.')
        data['items'].append(new_data)
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
# except FileNotFoundError:
#     with open(filename,'w') as file: json.dump({'items': [new_data]}, file, indent=4)


'''program reaching into memory space, crowd strike detection, 
detect chrome extension usage,,, pass the cookie/ ((token)) for reusage'''
#   user id
def create_user(user: str, ver_acc: str) -> User:
    print(user, 'your account is;', ver_acc)
    if ver_acc not in {'low', 'mid', 'high'}:
        raise ValueError("Invalid account level")
    print(user, 'your account is: ', ver_acc)
    return  User(
        user=user,
        account_level=ver_acc
    )
def token_attributes() -> set[action]:
    actions: set[action] = set()
    print("|_ This is about to set rwe permissions for the account _|")
    if input("  can this account execute? (y/n): ").lower() == 'y':
        actions.add('execute')
    if input("  can this account read? (y/n): ").lower() == 'y':
        actions.add('read')
    if input("  can this account write? (y/n): ").lower() == 'y':
        actions.add('write')
    print('Access actions: ', actions)
    return actions

def declare_tokens(user_token: str, token_permission: permission, actions: set[action]) -> Token:
    if user_token == 'y':
        if token_permission not in {'access', 'denied'}:
            raise ValueError('Token permission must be "access" or "denied"')
    elif user_token == 'n':
        print('... create temporary user token...')
    else:
        print('flag session')
    return Token(
        token=user_token.lower(), 
        permission=token_permission, 
        actions=actions)

def collect_cookies() -> list[str]:
    cookies: list[str] = []
    while True:
        user_cookie = input('What cookies? (good [cycles unnecessary], bad [exit loop])> ').lower()
        cookies.append(user_cookie)
        print(cookies)
        if user_cookie == 'bad':
            break
        elif user_cookie == 'good':
            continue
        else:
            print('Rerun analysis.\n')
    return cookies
def can(token: Token, action: action) -> bool:
    if token.permission != 'access':
        return False
    return action in token.actions

#   Session
''' 
Instead of reading temporary data collected in terminal this should verify back with 
database to check user is in the system and is authorized to perform requested functions
This login is executed in a cmd terminal
'''

def token_flow() -> Session:
    print('|_ sign-in _|')
#   user id
    user = input('Enter id (does nothing); ')
    ver_acc = input('What is account level (low, mid, high); ')
#   user id
    user = create_user(user, ver_acc) # creates a key pair check
    print('|_ Start process _|')
    description = input('describe (is not used); ')
    
    print('|_ step 1: key _|')
    user_token = input('Is there a token? ["y/n" (checks existence of user token)]> ')
    token_permission = input('What can this token do? ["access/denied" (serves no fn)]> ')
    actions = token_attributes()
    token = declare_tokens(user_token, token_permission, actions)

#   Session
    session = Session(user=user, token=token, cookies=[])
    if can(session.token, 'execute'):
        print('Token allows execute - collecting cookies')
        cookies = collect_cookies()
    else:
        print('Permission denied')
        cookies = []
    print('step 2: search')
    
    print('process: complete')
    filepath = str(DATA_DIR / "home_page.json")
    filename = filepath
    data = asdict(session)
    save_json_data(filepath, data)
    new_data = session
    append_to_json(new_data, filename)

#   Session
    return Session(user=user, token=token, cookies=cookies)
if __name__ == ('__main__'):
    session = token_flow()
    print(session)