#!/usr/bin/env python3

import subprocess
import os
import sys
from pathlib import Path
import getpass

def install_system_dependencies():
    """Install required system dependencies"""
    try:
        print("Installing system dependencies...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run([
            "sudo", "apt-get", "install", "-y",
            "pkg-config", "libmysqlclient-dev", "python3-dev",
            "build-essential", "mariadb-client", "mariadb-server",
            "git", "python3-pip", "python3-setuptools", "python3-venv"
        ], check=True)
        print("System dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install system dependencies: {e}")
        raise

def create_bench(bench_name, bench_path):
    """Create a new Frappe bench with version 15"""
    try:
        if not os.path.exists(bench_path):
            print(f"Creating new bench '{bench_name}' at {bench_path}...")
            install_system_dependencies()
            
            # Create bench with version 15
            subprocess.run([
                "bench", "init", bench_name,
                "--frappe-branch", "version-15",
                "--python", "python3"
            ], cwd=os.path.dirname(bench_path), check=True)
            print(f"Bench '{bench_name}' created successfully with Frappe version 15")
            
            os.chdir(bench_path)
            # Install frappe
            subprocess.run(["bench", "get-app", "frappe"], check=True)
            print("Installed frappe in the new bench")
        else:
            print(f"Bench already exists at {bench_path}")
            os.chdir(bench_path)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create bench: {e}")
        raise

def create_site(bench_path, site_name, admin_password):
    """Create a new site in the bench"""
    try:
        os.chdir(bench_path)
        if not os.path.exists(f"{bench_path}/sites/{site_name}"):
            print(f"Creating site '{site_name}'...")
            subprocess.run([
                "bench", "new-site", site_name,
                "--admin-password", admin_password,
                "--no-mariadb-socket"
            ], check=True)
            print(f"Site '{site_name}' created successfully")
            
            # Enable developer mode
            subprocess.run([
                "bench", "--site", site_name, "set-config", "developer_mode", "1"
            ], check=True)
            print(f"Developer mode enabled for site: {site_name}")

            # Set site configuration
            subprocess.run([
                "bench", "--site", site_name, "set-config", "host_name", site_name
            ], check=True)
            
            # Add site to hosts file
            hosts_entry = f"127.0.0.1\t{site_name}"
            try:
                with open("/etc/hosts", "r") as f:
                    hosts_content = f.read()
                
                if site_name not in hosts_content:
                    print(f"Adding {site_name} to hosts file...")
                    subprocess.run([
                        "sudo", "sh", "-c", f'echo "{hosts_entry}" >> /etc/hosts'
                    ], check=True)
                    print(f"Added {site_name} to hosts file")
            except Exception as e:
                print(f"Warning: Could not update hosts file: {e}")
                print(f"Please manually add this line to /etc/hosts: {hosts_entry}")

            # Set site as default
            subprocess.run([
                "bench", "use", site_name
            ], check=True)
            print(f"Set {site_name} as default site")
        else:
            print(f"Site '{site_name}' already exists")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create site: {e}")
        raise

def install_erpnext(bench_path, site_name):
    """Install ERPNext in the bench and site"""
    try:
        os.chdir(bench_path)
        print("Installing ERPNext...")
        subprocess.run(["bench", "get-app", "erpnext", "--branch", "version-15"], check=True)
        subprocess.run(["bench", "--site", site_name, "install-app", "erpnext"], check=True)
        print("ERPNext installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install ERPNext: {e}")
        raise

def install_custom_apps(bench_path, github_repos, site_name):
    """Install multiple custom apps from GitHub repositories"""
    try:
        os.chdir(bench_path)
        for repo in github_repos:
            if repo:
                print(f"Installing custom app from {repo}...")
                app_name = repo.split('/')[-1].replace('.git', '').replace('-', '_')
                subprocess.run(["bench", "get-app", repo, "--branch", "version-15"], check=True)
                subprocess.run(["bench", "--site", site_name, "install-app", app_name], check=True)
                print(f"App '{app_name}' installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install custom apps: {e}")
        raise

def get_user_input():
    """Get user input interactively."""
    print("\n=== Frappe Bench Setup Wizard ===\n")
    
    bench_name = input("Enter bench directory name: ").strip()
    while not bench_name:
        print("Bench name cannot be empty. Please try again.")
        bench_name = input("Enter bench directory name: ").strip()
    
    site_name = input("Enter site name (e.g., mysite.local): ").strip()
    while not site_name:
        print("Site name cannot be empty. Please try again.")
        site_name = input("Enter site name (e.g., mysite.local): ").strip()
    
    admin_password = getpass.getpass("Enter admin password: ").strip()
    while not admin_password:
        print("Password cannot be empty. Please try again.")
        admin_password = getpass.getpass("Enter admin password: ").strip()
    
    print("\nEnter GitHub repository URLs for custom apps (one per line)")
    print("Press Enter twice when done:")
    github_repos = []
    while True:
        repo = input().strip()
        if not repo:
            break
        github_repos.append(repo)
    
    return {
        'bench_name': bench_name,
        'site_name': site_name,
        'admin_password': admin_password,
        'github_repos': github_repos
    }

def main():
    try:
        # Get user input
        inputs = get_user_input()
        bench_path = os.path.join(os.getcwd(), inputs['bench_name'])
        
        # Create bench and site
        create_bench(inputs['bench_name'], bench_path)
        create_site(bench_path, inputs['site_name'], inputs['admin_password'])
        
        # Install ERPNext
        install_erpnext(bench_path, inputs['site_name'])
        
        # Install custom apps if any
        if inputs['github_repos']:
            install_custom_apps(bench_path, inputs['github_repos'], inputs['site_name'])
        
        print("\n=== Setup Completed Successfully! ===")
        print(f"✓ Bench directory: {bench_path}")
        print(f"✓ Site URL: http://{inputs['site_name']}:8000")
        print(f"✓ Admin password: {inputs['admin_password']}")
        print("\nTo start the bench, run:")
        print(f"cd {bench_path}")
        print("bench start")
        
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()






