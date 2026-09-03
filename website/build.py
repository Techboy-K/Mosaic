# -*- coding: utf-8 -*-
"""Build the whole site: public pages, landing film, crew portal, then stamp
asset URLs with content hashes so a deployed change is never served stale.

    python3 build.py
"""
import runpy, sys, os

W = os.path.dirname(os.path.abspath(__file__))
os.chdir(W)
sys.path.insert(0, W)

for step in ('pages_home', 'pages_rest', 'pages_landing', 'crew_pages'):
    print('--', step)
    runpy.run_module(step, run_name='__main__')

print('-- version-assets')
sys.exit(runpy.run_path(os.path.join(W, 'version-assets.py'), run_name='__main__') and 0)
