#!/usr/bin/env python3
import subprocess
import re
import sys

def get_current_version():
    """Gets the current version from pyproject.toml"""
    result = subprocess.run(['poetry', 'version', '--short'], 
                          capture_output=True, text=True, check=True)
    return result.stdout.strip()

def bump_version(bump_type='patch'):
    """Increments the package version
    
    Args:
        bump_type: Type of increment (major, minor, patch)
    """
    valid_bump_types = ['major', 'minor', 'patch', 'premajor', 'preminor', 'prepatch', 'prerelease']
    if bump_type not in valid_bump_types:
        raise ValueError(f"Bump type must be one of {valid_bump_types}")
    
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Increment the version
    result = subprocess.run(['poetry', 'version', bump_type], 
                          capture_output=True, text=True, check=True)
    new_version = get_current_version()
    print(f"New version: {new_version}")
    
    # Update version in __init__.py
    update_init_version(new_version)
    
    return new_version

def update_init_version(new_version):
    """Updates the version in __init__.py file"""
    init_path = 'bybit_history/__init__.py'
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Replace version using regular expression
    new_content = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"', content)
    
    with open(init_path, 'w') as f:
        f.write(new_content)
    
    print(f"Updated version in {init_path}")

def build_and_publish():
    """Builds and publishes the package to PyPI"""
    # Build the package
    subprocess.run(['poetry', 'build'], check=True)
    
    # Publish the package
    print("Publishing package to PyPI...")
    try:
        subprocess.run(['poetry', 'publish'], check=True)
        print("Package successfully published!")
    except subprocess.CalledProcessError:
        print("Error publishing package.")
        print("Make sure you have configured authentication for PyPI:")
        print("1. poetry config pypi-token.pypi YOUR_API_TOKEN")
        print("   or")
        print("2. poetry config http-basic.pypi username password")
        sys.exit(1)

def commit_changes(version):
    """Commits changes to git"""
    try:
        subprocess.run(['git', 'add', 'pyproject.toml', 'bybit_history/__init__.py'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Bump version to {version}'], check=True)
        print(f"Changes committed with message 'Bump version to {version}'")
    except subprocess.CalledProcessError:
        print("Error committing changes.")

def main():
    bump_type = 'patch'  # By default, increment patch version
    
    # If command line argument is provided, use it
    if len(sys.argv) > 1 and sys.argv[1] in ['major', 'minor', 'patch']:
        bump_type = sys.argv[1]
    
    try:
        new_version = bump_version(bump_type)
        build_and_publish()
        commit_changes(new_version)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 