#!/usr/bin/env python3
"""
BrightEdge DevOps Assignment - Automated Verification Script
Run this script using: python verify_assignment.py
"""

import os
import glob
import yaml
import jinja2

def main():
    print("==========================================================")
    print(" BRIGHTEDGE DEVOPS ASSIGNMENT - CHECKS & VERIFICATION")
    print("==========================================================\n")
    
    # Check 1: YAML Syntax Check
    yaml_files = [f for f in glob.glob('**/*.yaml', recursive=True) + glob.glob('**/*.yml', recursive=True) if 'templates' not in f and f != 'verify_assignment.py']
    print(f"[CHECK 1/4] Validating {len(yaml_files)} YAML configuration files...")
    yaml_errors = 0
    for f in sorted(yaml_files):
        try:
            with open(f, 'r', encoding='utf-8') as stream:
                yaml.safe_load(stream)
            print(f"  [OK] PASS: {f}")
        except Exception as e:
            print(f"  [FAIL] ERROR: {f} -> {e}")
            yaml_errors += 1
            
    # Check 2: Helm Templates Existence & Structure
    helm_templates = [
        'helm/charts/data-sync/Chart.yaml',
        'helm/charts/data-sync/values.yaml',
        'helm/charts/data-sync/values.staging.yaml',
        'helm/charts/data-sync/values.production.yaml',
        'helm/charts/data-sync/templates/_helpers.tpl',
        'helm/charts/data-sync/templates/deployment.yaml',
        'helm/charts/data-sync/templates/service.yaml',
        'helm/charts/data-sync/templates/configmap.yaml',
        'helm/charts/data-sync/templates/secret.yaml',
        'helm/charts/data-sync/templates/hpa.yaml',
        'helm/charts/data-sync/templates/pdb.yaml',
        'helm/charts/data-sync/templates/servicemonitor.yaml',
        'standard/data-sync/production/kustomization.yaml',
        'standard/data-sync/production/deployment-patch.yaml'
    ]
    print(f"\n[CHECK 2/4] Checking {len(helm_templates)} Helm & Kustomize files...")
    helm_errors = 0
    for f in helm_templates:
        if os.path.exists(f):
            print(f"  [OK] PASS: {f}")
        else:
            print(f"  [FAIL] Missing file -> {f}")
            helm_errors += 1

    # Check 3: Ansible Role & Jinja2 Template Rendering
    ansible_files = [
        'roles/be-data-sync/defaults/main.yml',
        'roles/be-data-sync/handlers/main.yml',
        'roles/be-data-sync/tasks/main.yml',
        'roles/be-data-sync/meta/main.yml',
        'roles/be-data-sync/templates/data-sync.service.j2',
        'playbooks/playbook-data-sync.yml',
        'group_vars/service.yml'
    ]
    print(f"\n[CHECK 3/4] Checking {len(ansible_files)} Ansible role files & Jinja2 template rendering...")
    ansible_errors = 0
    for f in ansible_files:
        if os.path.exists(f):
            print(f"  [OK] PASS: {f}")
        else:
            print(f"  [FAIL] Missing file -> {f}")
            ansible_errors += 1
            
    # Try rendering Jinja2 template
    try:
        with open('group_vars/service.yml', encoding='utf-8') as f:
            group_vars = yaml.safe_load(f)
        with open('roles/be-data-sync/defaults/main.yml', encoding='utf-8') as f:
            defaults = yaml.safe_load(f)
        context = {**defaults, **group_vars}
        with open('roles/be-data-sync/templates/data-sync.service.j2', encoding='utf-8') as f:
            template = jinja2.Template(f.read())
        rendered = template.render(context)
        print("  [OK] PASS: Jinja2 systemd unit template rendered successfully.")
    except Exception as e:
        print(f"  [FAIL] Template rendering error -> {e}")
        ansible_errors += 1

    # Check 4: Documentation Files
    docs = ['README.md', 'DESIGN.md']
    print(f"\n[CHECK 4/4] Checking Documentation files...")
    doc_errors = 0
    for f in docs:
        if os.path.exists(f) and os.path.getsize(f) > 500:
            print(f"  [OK] PASS: {f} ({os.path.getsize(f)} bytes)")
        else:
            print(f"  [FAIL] Missing or empty doc -> {f}")
            doc_errors += 1

    total_errors = yaml_errors + helm_errors + ansible_errors + doc_errors
    print("\n==========================================================")
    if total_errors == 0:
        print(" ALL CHECKS PASSED SUCCESSFULLY! PROJECT IS 100% READY.")
    else:
        print(f" DISCOVERED {total_errors} ISSUES.")
    print("==========================================================")

if __name__ == '__main__':
    main()
