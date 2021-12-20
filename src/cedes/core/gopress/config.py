# -*- coding: utf-8 -*-

import os

# go4web '5a3cb62a37d3d669dba2e655de'
# cedes '5a3cb62a37d3d669dba2e655de'
GOPRESS_APIKEY = '5a3cb62a37d3d669dba2e655de'
# go4web 'support@go4web.be'
# cedes 'cedes@unamur.be'
GOPRESS_EMAIL = 'support@go4web.be'
GOPRESS_URL = 'https://ws.gopress.be'

DATA_PATH = os.environ['BUILDOUT_DIRECTORY']
GOPRESS_PATH = os.path.join(DATA_PATH, 'var/gopress')
GOPRESS_XML_FILE_PATH = os.path.join(GOPRESS_PATH, "metadatas.xml")

GOPRESS_DO_BACKUP = True
GOPRESS_BACKUP_PATH = os.path.join(GOPRESS_PATH, 'backups')

PRINT_GOPRESS_REQUEST = False
FOLDER_TO_PRINT = ''
ARTICLE_TO_PRINT = ''


def create_xml_file():
    if not os.path.exists(GOPRESS_PATH):
        os.mkdir(GOPRESS_PATH)
    if not os.path.exists(GOPRESS_XML_FILE_PATH):
        xmlfile = open(GOPRESS_XML_FILE_PATH, 'w')
        xmlfile.write('<PB></PB>')
        xmlfile.close()
