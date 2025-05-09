#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import subprocess
import os
import sys
from pathlib import Path
import getpass

class FrappeSetupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Frappe Bench Setup Wizard")
        self.root.geometry("800x600")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input fields
        ttk.Label(self.main_frame, text="Bench Directory Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.bench_name = ttk.Entry(self.main_frame, width=40)
        self.bench_name.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(self.main_frame, text="Site Name (e.g., mysite.local):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.site_name = ttk.Entry(self.main_frame, width=40)
        self.site_name.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(self.main_frame, text="Admin Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.admin_password = ttk.Entry(self.main_frame, width=40, show="*")
        self.admin_password.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(self.main_frame, text="MySQL Root Password:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.mysql_password = ttk.Entry(self.main_frame, width=40, show="*")
        self.mysql_password.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(self.main_frame, text="GitHub Repositories (one per line):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.github_repos = scrolledtext.ScrolledText(self.main_frame, width=40, height=5)
        self.github_repos.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Progress section
        ttk.Label(self.main_frame, text="Progress:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.progress_text = scrolledtext.ScrolledText(self.main_frame, width=60, height=15)
        self.progress_text.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.main_frame, length=300, mode='determinate')
        self.progress_bar.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # User input for future interactivity
        ttk.Label(self.main_frame, text="Input:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.user_input = ttk.Entry(self.main_frame, width=40)
        self.user_input.grid(row=7, column=1, sticky=tk.W, pady=5)
        self.user_input.bind('<Return>', self.send_user_input)
        self.user_input.config(state='disabled')
        
        # Start button
        self.start_button = ttk.Button(self.main_frame, text="Start Setup", command=self.start_setup)
        self.start_button.grid(row=8, column=1, sticky=tk.E, pady=10)
        
        # Message queue for thread-safe updates
        self.queue = queue.Queue()
        self.root.after(100, self.check_queue)

    def update_progress(self, message):
        self.queue.put(message)

    def check_queue(self):
        while True:
            try:
                message = self.queue.get_nowait()
                self.progress_text.insert(tk.END, message + "\n")
                self.progress_text.see(tk.END)
            except queue.Empty:
                break
        self.root.after(100, self.check_queue)

    def send_user_input(self, event=None):
        # Placeholder for future interactive commands
        value = self.user_input.get()
        self.update_progress(f"[User Input]: {value}")
        self.user_input.delete(0, tk.END)
        # In future, send this to the subprocess if needed

    def run_command(self, cmd, input_text=None, env=None):
        """Run a command and yield output line by line."""
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE if input_text else None, text=True, env=env)
        if input_text:
            process.stdin.write(input_text + '\n')
            process.stdin.flush()
        for line in iter(process.stdout.readline, ''):
            self.update_progress(line.rstrip())
        process.stdout.close()
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd)

    def start_setup(self):
        # Disable start button
        self.start_button.state(['disabled'])
        self.user_input.config(state='normal')
        
        # Clear progress
        self.progress_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        
        # Get input values
        bench_name = self.bench_name.get().strip()
        site_name = self.site_name.get().strip()
        admin_password = self.admin_password.get().strip()
        mysql_password = self.mysql_password.get().strip()
        github_repos = [repo.strip() for repo in self.github_repos.get(1.0, tk.END).splitlines() if repo.strip()]
        
        # Validate inputs
        if not all([bench_name, site_name, admin_password, mysql_password]):
            messagebox.showerror("Error", "Please fill in all required fields")
            self.start_button.state(['!disabled'])
            self.user_input.config(state='disabled')
            return
        
        # Start setup in a separate thread
        thread = threading.Thread(target=self.run_setup, args=(bench_name, site_name, admin_password, mysql_password, github_repos))
        thread.daemon = True
        thread.start()

    def run_setup(self, bench_name, site_name, admin_password, mysql_password, github_repos):
        try:
            bench_path = os.path.join(os.getcwd(), bench_name)
            
            # Install system dependencies
            self.update_progress("Installing system dependencies...")
            self.install_system_dependencies()
            self.progress_bar['value'] = 10
            
            # Create bench
            self.update_progress(f"Creating bench '{bench_name}'...")
            self.create_bench(bench_name, bench_path)
            self.progress_bar['value'] = 30
            
            # Create site
            self.update_progress(f"Creating site '{site_name}'...")
            self.create_site(bench_path, site_name, admin_password, mysql_password)
            self.progress_bar['value'] = 50
            
            # Install ERPNext
            self.update_progress("Installing ERPNext...")
            self.install_erpnext(bench_path, site_name)
            self.progress_bar['value'] = 70
            
            # Install custom apps
            if github_repos:
                self.update_progress("Installing custom apps...")
                self.install_custom_apps(bench_path, github_repos, site_name)
            self.progress_bar['value'] = 90
            
            # Setup complete
            self.update_progress("\n=== Setup Completed Successfully! ===")
            self.update_progress(f"✓ Bench directory: {bench_path}")
            self.update_progress(f"✓ Site URL: http://{site_name}:8000")
            self.update_progress(f"✓ Admin password: {admin_password}")
            self.update_progress("\nTo start the bench, run:")
            self.update_progress(f"cd {bench_path}")
            self.update_progress("bench start")
            
            self.progress_bar['value'] = 100
            messagebox.showinfo("Success", "Setup completed successfully!")
            
        except Exception as e:
            self.update_progress(f"\nError during setup: {str(e)}")
            messagebox.showerror("Error", f"Setup failed: {str(e)}")
        finally:
            self.start_button.state(['!disabled'])
            self.user_input.config(state='disabled')

    def install_system_dependencies(self):
        try:
            self.run_command(["sudo", "apt-get", "update"])
            self.run_command([
                "sudo", "apt-get", "install", "-y",
                "pkg-config", "libmysqlclient-dev", "python3-dev",
                "build-essential", "mariadb-client", "mariadb-server",
                "git", "python3-pip", "python3-setuptools", "python3-venv"
            ])
            self.update_progress("System dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            self.update_progress(f"Failed to install system dependencies: {e}")
            raise

    def create_bench(self, bench_name, bench_path):
        try:
            if not os.path.exists(bench_path):
                self.run_command([
                    "bench", "init", bench_name,
                    "--frappe-branch", "version-15",
                    "--python", "python3"
                ])
                self.update_progress(f"Bench '{bench_name}' created successfully")
                
                os.chdir(bench_path)
                # self.run_command(["bench", "get-app", "frappe"])
                self.update_progress("Frappe installed successfully")
            else:
                self.update_progress(f"Bench already exists at {bench_path}")
                os.chdir(bench_path)
        except subprocess.CalledProcessError as e:
            self.update_progress(f"Failed to create bench: {e}")
            raise

    def create_site(self, bench_path, site_name, admin_password, mysql_password):
        try:
            os.chdir(bench_path)
            if not os.path.exists(f"{bench_path}/sites/{site_name}"):
                self.run_command([
                    "bench", "new-site", site_name,
                    "--admin-password", admin_password,
                    "--mariadb-root-password", mysql_password,
                    "--no-mariadb-socket"
                ])
                self.update_progress(f"Site '{site_name}' created successfully")
                
                self.run_command([
                    "bench", "--site", site_name, "set-config", "developer_mode", "1"
                ])
                
                self.run_command([
                    "bench", "--site", site_name, "set-config", "host_name", site_name
                ])
                
                hosts_entry = f"127.0.0.1\t{site_name}"
                try:
                    with open("/etc/hosts", "r") as f:
                        hosts_content = f.read()
                    
                    if site_name not in hosts_content:
                        self.run_command([
                            "sudo", "sh", "-c", f'echo "{hosts_entry}" >> /etc/hosts'
                        ])
                        self.update_progress(f"Added {site_name} to hosts file")
                except Exception as e:
                    self.update_progress(f"Warning: Could not update hosts file: {e}")
                    self.update_progress(f"Please manually add this line to /etc/hosts: {hosts_entry}")
                
                self.run_command(["bench", "use", site_name])
                self.update_progress(f"Set {site_name} as default site")
            else:
                self.update_progress(f"Site '{site_name}' already exists")
        except subprocess.CalledProcessError as e:
            self.update_progress(f"Failed to create site: {e}")
            raise

    def install_erpnext(self, bench_path, site_name):
        try:
            os.chdir(bench_path)
            self.run_command(["bench", "get-app", "erpnext", "--branch", "version-15"])
            self.run_command(["bench", "--site", site_name, "install-app", "erpnext"])
            self.update_progress("ERPNext installed successfully")
        except subprocess.CalledProcessError as e:
            self.update_progress(f"Failed to install ERPNext: {e}")
            raise

    def install_custom_apps(self, bench_path, github_repos, site_name):
        try:
            os.chdir(bench_path)
            for repo in github_repos:
                if repo:
                    self.update_progress(f"Installing custom app from {repo}...")
                    app_name = repo.split('/')[-1].replace('.git', '').replace('-', '_')
                    self.run_command(["bench", "get-app", repo, "--branch", "version-15"])
                    self.run_command(["bench", "--site", site_name, "install-app", app_name])
                    self.update_progress(f"App '{app_name}' installed successfully")
        except subprocess.CalledProcessError as e:
            self.update_progress(f"Failed to install custom apps: {e}")
            raise

def main():
    root = tk.Tk()
    app = FrappeSetupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 