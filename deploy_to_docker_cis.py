#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import os
import shutil
import traceback
import requests
import pathlib
from requests.auth import HTTPBasicAuth
from sys import exit

hostname = "127.0.0.1"
portnum = 10001

source_folder = os.getcwd()
cis_server_folder = "{}/cis-docker-compose-env/server-data".format(
    pathlib.Path(__file__).parent.resolve()
)
target_folder = "{}/workspace/internal/default/component".format(
    cis_server_folder
)
wid = "internal:default/default"
# wid = ""

# Todo: 1 Add files here to be deployed to CIS server/workspace
files_to_deploy = [
    (source_folder, target_folder, "template_for_cis.py")
    # (source_folder, target_folder, 'my_component_for_cis.py'),
]


def deploy_local():
    try:

        for tup in files_to_deploy:
            source_file = os.path.join(tup[0], tup[2])
            target_file = os.path.join(tup[1], tup[2])
            shutil.copyfile(source_file, target_file)
            print("File copied: ", target_file)

            source_file = os.path.join(
                tup[0],
                tup[2],
            )
            target_file = os.path.join(tup[1], u"{}.edited".format(tup[2]))
            shutil.copyfile(source_file, target_file)
            # print("File copied: ", target_file)

        reload_workspace()
    except Exception as exc:
        print(traceback.format_exc())
        print(str(exc))


def reload_workspace():
    print("Reloading workspace...")
    try:
        if len(wid) > 0:

            execute = "http://%s:%s/reload_workspace?confirm=false&wid=%s" % (
                hostname,
                portnum,
                wid,
            )
            print("Reload executing:%s" % execute)
            requests.post(
                "http://%s:%s/reload_workspace?confirm=false&wid=%s"
                % (hostname, portnum, wid),
                verify=False,
                auth=HTTPBasicAuth("support", "support"),
            )
            print("Workspace %s was reloaded." % wid)
        else:
            print("Reloading ALL workspaces")
            requests.post(
                "http://support:support@%s:%s/reload_workspaces?confirm=False"
                % (hostname, portnum),
                verify=False,
                auth=HTTPBasicAuth("support", "support"),
            )
            print("All Workspaces was reloaded")
    except Exception as e:
        print(str(e))
        exit(-1)


if __name__ == "__main__":
    print("Source folder: ", source_folder)
    deploy_local()
