#!/usr/bin/env python3
import subprocess
import re
import sys

def get_current_version():
    """Получает текущую версию из pyproject.toml"""
    result = subprocess.run(['poetry', 'version', '--short'], 
                          capture_output=True, text=True, check=True)
    return result.stdout.strip()

def bump_version(bump_type='patch'):
    """Инкрементирует версию пакета
    
    Args:
        bump_type: Тип инкрементирования (major, minor, patch)
    """
    valid_bump_types = ['major', 'minor', 'patch', 'premajor', 'preminor', 'prepatch', 'prerelease']
    if bump_type not in valid_bump_types:
        raise ValueError(f"Тип инкрементирования должен быть одним из {valid_bump_types}")
    
    current_version = get_current_version()
    print(f"Текущая версия: {current_version}")
    
    # Инкрементируем версию
    result = subprocess.run(['poetry', 'version', bump_type], 
                          capture_output=True, text=True, check=True)
    new_version = get_current_version()
    print(f"Новая версия: {new_version}")
    
    # Обновляем версию в __init__.py
    update_init_version(new_version)
    
    return new_version

def update_init_version(new_version):
    """Обновляет версию в файле __init__.py"""
    init_path = 'bybit_history/__init__.py'
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Замена версии с помощью регулярного выражения
    new_content = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"', content)
    
    with open(init_path, 'w') as f:
        f.write(new_content)
    
    print(f"Обновлена версия в {init_path}")

def build_and_publish():
    """Собирает и публикует пакет в PyPI"""
    # Собираем пакет
    subprocess.run(['poetry', 'build'], check=True)
    
    # Публикуем пакет
    print("Публикация пакета в PyPI...")
    try:
        subprocess.run(['poetry', 'publish'], check=True)
        print("Пакет успешно опубликован!")
    except subprocess.CalledProcessError:
        print("Ошибка при публикации пакета.")
        print("Убедитесь, что вы настроили аутентификацию для PyPI:")
        print("1. poetry config pypi-token.pypi YOUR_API_TOKEN")
        print("   или")
        print("2. poetry config http-basic.pypi username password")
        sys.exit(1)

def commit_changes(version):
    """Коммитит изменения в git"""
    try:
        subprocess.run(['git', 'add', 'pyproject.toml', 'bybit_history/__init__.py'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Bump version to {version}'], check=True)
        print(f"Изменения закоммичены с сообщением 'Bump version to {version}'")
    except subprocess.CalledProcessError:
        print("Ошибка при коммите изменений.")

def main():
    bump_type = 'patch'  # По умолчанию инкрементируем patch версию
    
    # Если указан аргумент командной строки, используем его
    if len(sys.argv) > 1 and sys.argv[1] in ['major', 'minor', 'patch']:
        bump_type = sys.argv[1]
    
    try:
        new_version = bump_version(bump_type)
        build_and_publish()
        commit_changes(new_version)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 