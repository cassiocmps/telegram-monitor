import os
import signal
from src.config import keywords

CONFIG_PATH = 'src/config.py'

def save_keywords_to_config(new_keywords):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        in_keywords = False
        for line in lines:
            if line.strip().startswith('keywords = ['):
                in_keywords = True
                f.write('keywords = [\n')
                for group in new_keywords:
                    f.write(f"    {group},\n")
            elif in_keywords:
                if line.strip().startswith(']'):
                    in_keywords = False
                    f.write(']\n')
            else:
                f.write(line)

def keyword_console_manager():
    global keywords
    while True:
        cmd = input('\n1. Add keyword group\n2. Delete keyword group\n3. List keyword groups\n4. Exit\nSelect option [1-4]: ').strip()
        if cmd == '1':
            group = input('Enter keyword group (comma separated): ').strip()
            group_list = [w.strip() for w in group.split(',') if w.strip()]
            if group_list:
                keywords.append(group_list)
                save_keywords_to_config(keywords)
                print(f"Added: {group_list}")
        elif cmd == '2':
            for idx, group in enumerate(keywords):
                print(f"{idx}: {group}")
            idx = input('Enter index to delete: ').strip()
            if idx.isdigit() and 0 <= int(idx) < len(keywords):
                removed = keywords.pop(int(idx))
                save_keywords_to_config(keywords)
                print(f"Removed: {removed}")
            else:
                print("Invalid index.")
        elif cmd == '3':
            for idx, group in enumerate(keywords):
                print(f"{idx}: {group}")
        elif cmd == '4':
            print('Exiting keyword manager and terminating bot.')
            os.kill(os.getpid(), signal.SIGINT)
            break
        else:
            print("Unknown option. Please select 1, 2, 3, or 4.")
