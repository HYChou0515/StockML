import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

RESOURCE_ROOT = os.path.join(PROJECT_ROOT, 'resource')
if not os.path.exists(RESOURCE_ROOT):
    os.mkdir(RESOURCE_ROOT)

