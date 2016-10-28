# Copyright 2016 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Copyright 2016 VMware, Inc.  All rights reserved. 
Licensed under the Apache License, Version 2.0 
http://www.apache.org/licenses/LICENSE-2.0
"""
__author__ = "VMware, Inc"

import os
import traceback 

import logging
import sys
import copy


from pyVmomi import Vim, vim, vmodl
from MoManager import GetMoManager

sys.path.append('/usr/lib/vmware/hostd/hmo/')
sys.path.append('/usr/lib/vmware/vsan/perfsvc/')

# FFU: Needed for long running tasks:
#import VsanTaskTracker
#import VsanTaskTrackerImpl

logger = logging.getLogger()

class VsanDockerPersistentVolumeSystemImpl(vim.host.VsanDockerPersistentVolumeSystem):
    '''Example Implementation of DockVol ESX VMODL support'''

    def __init__(self, moId):
        vim.host.VsanDockerPersistentVolumeSystem.__init__(self, moId)


    def GetTenantList(self):
        logger.info("Running GetTenantList() method")
        try:
            ## fetch data from DB
            # Note: we should be using HostD tasks for long running work.
            # See usage of CreateRunHostdTask in  VSAN .py code. 
            # For now, we do blocking calls
            output = ["Tenant", "TenantWhoCares", "super Tenant"]
            logger.info("list of tenants: %s" % output)

            # now place it in the output type and return the result
            result = vim.vsan.VsanDockerPersistentVolumeTenantList()
            result.tenants = output
            return result 
        except:
            logger.info("Failed to fetch tenants list", exc_info=1)
     
    def GetDatastoreAccessPrivileges(self):
        logger.info("Running GetDatastoreAccessPrivileges() method")
        #result = vim.vsan.VsanDockerPersistentVolumeTenantList()
        result = vim.vsan.VsanDockerPersistentVolumeDatastoreAccessPrivileges()

        try:
            ## fetch data from DB (fake it for now)
            # Note: we should be using HostD tasks for long running work.
            # See usage of CreateRunHostdTask in  VSAN .py code. 
            # For now, we do blocking calls
                        
            result.datastore = "datastore1"
            result.create_volumes = True
            result.delete_volumes = False
            result.mount_volumes = True
            result.max_volume_size = '500MB'
            result.usage_quota = '1TB'
        except:
            logger.info("Failed to fetch datastore access privileges", exc_info=1)
        return result 
    
    def CreateDatastoreAccessPrivileges(self, datastore, create_volumes, delete_volumes, mount_volumes, max_volume_size, usage_quota):
        result = vim.vsan.VsanDockerPersistentVolumeDatastoreAccessPrivileges()
        try:
        # Currently, just fake it
        # Need to call corressponding API in auth_data.py
        # now just return the object
            result.datastore = datastore
            result.create_volumes = create_volumes
            result.delete_volumes = delete_volumes
            result.mount_volumes = mount_volumes
            result.max_volume_size = max_volume_size
            result.usage_quota = usage_quota
        except:
            logger.info("Failed to create datastore access privileges", exc_info=1)

        return result 
    
    def CreateTenant(self, name, description, default_datastore, default_privileges=None, vms=None, privileges=None):
        result = vim.vsan.VsanDockerPersistentVolumeTenant()
        try:
        # Currently, just fake it
        # Need to call corressponding API in auth_data.py
        # now just return the object
            result.name = name
            result.description = description
            result.default_datastore = default_datastore
            #result.default_privileges = default_privileges
            #result.vms = copy.deepcopy(vms)
            #result.privileges = copy.deepcopy(privileges)
        except:
            logger.info("Failed to create datastore access privileges", exc_info=1)

        return result 

GetMoManager().RegisterObjects([VsanDockerPersistentVolumeSystemImpl("vsan-docker-persistent-volumes")])
