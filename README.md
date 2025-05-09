# Frappe Bench Setup Automation

This script automates the setup of a Frappe Bench environment with ERPNext and custom apps.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- Git
- System dependencies for Frappe Bench (refer to [Frappe Bench documentation](https://frappeframework.com/docs/user/en/installation))

## Usage

Run the script with the following command:

```bash
python3 frappe_bench_setup.py --bench-name <bench_name> --site-name <site_name> --admin-password <password> [--github-repo <repository_url>]
```

### Arguments

- `--bench-name`: Name of the bench directory to create (required)
- `--site-name`: Name of the site to create (required)
- `--admin-password`: Admin password for the site (required)
- `--github-repo`: GitHub repository URL for custom app (optional)

### Example

```bash
python3 frappe_bench_setup.py --bench-name mybench --site-name mysite.local --admin-password admin123 --github-repo https://github.com/username/custom-app.git
```

## What the Script Does

1. Installs Frappe Bench if not already installed
2. Creates a new bench directory with Frappe version 15
3. Creates a new site with the specified name and admin password
4. Installs ERPNext
5. If a GitHub repository is provided, installs the custom app from that repository
6. Provides information about the setup and how to start the bench

## Notes

- Make sure you have all the system dependencies installed before running the script
- The script will create the bench in the current directory
- The site will be accessible at `http://<site_name>:8000` after starting the bench 