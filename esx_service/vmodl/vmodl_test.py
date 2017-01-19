#!/usr/bin/env python

# Copyright 2016 VMWare, Inc. All Rights Reserved.
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

# An example of connecting to (local) VSAN SIMS and fetching simple data 
# from VSAN and VsphereContainerService
#
# Usage: 
#
# 1. Drop VsphereContainerService*py files to 
#       /lib/python2.7/site-packages/pyMo/vim/vsan or 
#       /lib64/python3.5/site-packages/pyMo/vim/vsan
#    Do not forget /etc/init.d/vsanmgmtd restart
# 
# 1a. Drop the file below (vmodl_test.py) in local folder or wherever import works from 
#
# 2. In Python, run the following:
# import vmodl_test
# stub = vmodl_test.connect_to_vcs()
# vmodl_test.get_tenants(stub)       # print tenant list

import socket
import sys
sys.path.append('/lib64/python3.5/site-packages/pyMo/vim/vsan')
sys.path.append('/lib/python2.7/site-packages/pyMo/vim/vsan')

import pyVim
import pyVim.connect
import pyVim.host
import pyVmomi
import pyVmomi.VmomiSupport
from pyVmomi import vim
from vsanPerfPyMo import VsanPerformanceManager
import random
import unittest
import log_config
import vmdk_ops
import vmdk_ops_test
import vmdk_utils
import VsphereContainerService

si = None

TENANT_NAME = "TEST_TENANT_NAME"
TENANT_DESC = "TEST_TENANT_DESCRIPTION"
NEW_TENANT_NAME = "TEST_TENANT_NAME_2"
NEW_TENANT_DESC = "TEST_TENANT_DESCRIPTION_2"
TENANT_PREFIX = "TEST_TENANT_"

def connect_to_vcs(host="localhost", port=443):
    """
    Connect to VCS - currently utilizing VSAN mgmt service on ESX (/vsan) - and return SOAP stub
    """

    si = vmdk_ops.get_si()
    #pylint: disable=no-member
    hostSystem = pyVim.host.GetHostSystem(si)

    token = hostSystem.configManager.vsanSystem.FetchVsanSharedSecret()

    version = pyVmomi.VmomiSupport.newestVersions.Get("vim")
    stub = pyVmomi.SoapStubAdapter(host=host,
                                   port=443,
                                   version=version,
                                   path="/vsan",
                                   poolSize=0)
    vpm = vim.cluster.VsanPerformanceManager("vsan-performance-manager", stub)
    logged_in = vpm.Login(token)

    if not logged_in:
        print("Failed to get sims stub for host %s" % host)
        raise OSError("Failed to login to VSAN mgmt server")

    return stub

def get_tenants(stub):
    vcs = vim.vcs.VsphereContainerService("vsphere-container-service", stub)
    tenantMgr = vcs.GetTenantManager()
    return tenantMgr.GetTenants()

class TestVsphereContainerService(unittest.TestCase):
    """
    Unit tests for VsphereContainerServiceImpl
    """

    vcs = None
    tenantMgr = None

    random_id = random.randint(0, 65536)
    vm1_name = 'vm1_name_' + str(random_id)
    vm1 = None

    random_id = random.randint(0, 65536)
    vm2_name = 'vm2_name_' + str(random_id)
    vm2 = None

    datastore = None
    datastore2 = None

    @classmethod
    def setUpClass(cls):
        ip = socket.gethostbyname(socket.gethostname())
        stub = connect_to_vcs(host=ip, port=443)
        cls.vcs = vim.vcs.VsphereContainerService("vsphere-container-service", stub)
        cls.tenantMgr = cls.vcs.GetTenantManager()
        cls.setup_datastore()
        cls.create_vms()

    @classmethod
    def setup_datastore(cls):
        datastores = vmdk_utils.get_datastore_objects()
        if datastores:
            cls.datastore = datastores[0].info.name
            if len(datastores) > 1:
                cls.datastore2 = datastores[1].info.name
        else:
            cls.fail("Datastore is not available!")

    @classmethod
    def create_vms(cls):
        si = vmdk_ops.get_si()
        error, cls.vm1 = vmdk_ops_test.create_vm(si=si, 
                                                 vm_name=cls.vm1_name, 
                                                 datastore_name=cls.datastore)
        if error:
            cls.fail("Failed to create VM1!")

        error, cls.vm2 = vmdk_ops_test.create_vm(si=si, 
                                                 vm_name=cls.vm2_name, 
                                                 datastore_name=cls.datastore)
        if error:
            cls.fail("Failed to create VM2!")

    @classmethod
    def tearDownClass(cls):
        """ Cleanup after all tests """
        cls.cleanup_vms()

    @classmethod
    def cleanup_vms(cls):
        si = vmdk_ops.get_si()
        vmdk_ops_test.remove_vm(si, cls.vm1)
        vmdk_ops_test.remove_vm(si, cls.vm2)

    def tearDown(self):
        """ Cleanup after each test """
        self.cleanup_tenants()

    def cleanup_tenants(self):
        tenants = self.tenantMgr.GetTenants()
        for tenant in tenants:
            if tenant.name.startswith(TENANT_PREFIX):
                self.tenantMgr.RemoveTenant(tenant.name)

    def test_add_tenant(self):
        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Verify the result
        self.assertTrue(tenant)
        self.assertEqual(tenant.name, TENANT_NAME)
        self.assertEqual(tenant.description, TENANT_DESC)
        
    def test_get_tenant_by_name(self):
        # Create a tenant
        self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Get the tenant
        tenants = self.tenantMgr.GetTenants(name=TENANT_NAME)

        # Verify the result
        self.assertTrue(tenants)
        self.assertEqual(tenants[0].name, TENANT_NAME)
        self.assertEqual(tenants[0].description, TENANT_DESC)

    def test_get_all_tenants(self):
        # Create 2 tenants
        self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)
        self.tenantMgr.CreateTenant(name=NEW_TENANT_NAME, description=NEW_TENANT_NAME)

        # Get all tenants
        tenants = self.tenantMgr.GetTenants()

        # Verify the result
        self.assertTrue(tenants)
        self.assertEqual(len(tenants), 3) # plus DEFAULT tenant

    def test_remove_tenant(self):
        # Create a tenant
        self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Remove the tenant
        self.tenantMgr.RemoveTenant(name=TENANT_NAME)

        # Verify the result
        tenants = self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertFalse(tenants)

    def test_update_tenant(self):
        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Update the tenant
        self.tenantMgr.UpdateTenant(name=TENANT_NAME, new_name=NEW_TENANT_NAME, description=NEW_TENANT_DESC)

        # Verify the result
        tenants = self.tenantMgr.GetTenants(name=NEW_TENANT_NAME)
        self.assertTrue(tenants)
        self.assertEqual(tenants[0].name, NEW_TENANT_NAME)
        self.assertEqual(tenants[0].description, NEW_TENANT_DESC)

    def test_add_vms(self):
        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Add a VM to the tenant
        vms = [self.vm1_name]
        self.tenantMgr.AddVMs(tenant, vms)

        # Verify the result
        result=self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertTrue(result)
        self.assertEqual(result[0].vms, vms)

    def test_remove_vms(self):
        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Add 2 VMs to the tenant
        vms = [self.vm1_name, self.vm2_name]
        self.tenantMgr.AddVMs(tenant, vms)

        # Remove the VMs from the tenant
        self.tenantMgr.RemoveVMs(tenant, vms)

        # Verify the result
        result = self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertTrue(result)
        self.assertEqual(result[0].vms, [])

    def test_get_vms(self):
        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Add 2 VMs to the tenant
        vms = [self.vm1_name, self.vm2_name]
        self.tenantMgr.AddVMs(tenant, vms)

        # Verify the result
        result = self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertTrue(result)
        self.assertEqual(result[0].vms, vms)

    def test_replace_vms(self):
        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Add VM1 to the tenant
        vm1 = [self.vm1_name]
        self.tenantMgr.AddVMs(tenant, vm1)

        # Replace with VM2
        vm2 = [self.vm2_name]
        self.tenantMgr.ReplaceVMs(tenant, vm2)

        # Verify the result
        result = self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertTrue(result)
        vms = result[0].vms
        self.assertEqual(vms, vm2)

    def test_add_privilege(self):
        # Construct a datastore access privilege
        privilege = vim.vcs.storage.DatastoreAccessPrivilege()
        privilege.datastore =  self.datastore
        privilege.allow_create = True
        privilege.volume_max_size = 512
        privilege.volume_total_size = 1024

        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Add privilege to the tenant
        self.tenantMgr.AddPrivilege(tenant, privilege)

        # Verify the privilege
        result = self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertTrue(result)
        p = result[0].privileges
        self.assertTrue(p)
        self.assertEqual(p[0].datastore, self.datastore)
        self.assertEqual(p[0].allow_create, True)
        self.assertEqual(p[0].volume_max_size, 512)
        self.assertEqual(p[0].volume_total_size, 1024)

        # Verify the default datastore
        self.assertEqual(result[0].default_datastore, self.datastore)

    def test_remove_privilege(self):
        # Construct a datastore access privilege
        privilege = vim.vcs.storage.DatastoreAccessPrivilege()
        privilege.datastore =  self.datastore
        privilege.allow_create = True
        privilege.volume_max_size = 512
        privilege.volume_total_size = 1024

        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Add privilege to the tenant
        self.tenantMgr.AddPrivilege(tenant, privilege)

        # Remove privilege from the tenant
        self.tenantMgr.RemovePrivilege(tenant, self.datastore)

        # Verify the privilege
        result = self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertTrue(result)
        self.assertFalse(result[0].privileges)

        # Verify the default datastore
        self.assertFalse(result[0].default_datastore)

    def test_update_privilege(self):
        # Construct a datastore access privilege
        privilege = vim.vcs.storage.DatastoreAccessPrivilege()
        privilege.datastore =  self.datastore
        privilege.allow_create = True
        privilege.volume_max_size = 512
        privilege.volume_total_size = 1024

        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Add privilege to the tenant
        self.tenantMgr.AddPrivilege(tenant, privilege)

        # Update the privilege
        self.tenantMgr.UpdatePrivilege(tenant, self.datastore, allow_create=False, volume_max_size=1024, volume_total_size=2048)

        # Verify the privilege
        result = self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertTrue(result)
        p = result[0].privileges
        self.assertTrue(p)
        self.assertEqual(p[0].datastore, self.datastore)
        self.assertEqual(p[0].allow_create, False)
        self.assertEqual(p[0].volume_max_size, 1024)
        self.assertEqual(p[0].volume_total_size, 2048)

    def test_get_privileges(self):
        if not self.datastore2:
            return

        # Construct 2 datastore access privileges
        p1 = vim.vcs.storage.DatastoreAccessPrivilege()
        p1.datastore =  self.datastore
        p1.allow_create = True
        p1.volume_max_size = 512
        p1.volume_total_size = 1024

        p2 = vim.vcs.storage.DatastoreAccessPrivilege()
        p2.datastore =  self.datastore2
        p2.allow_create = False
        p2.volume_max_size = 1024
        p2.volume_total_size = 2048

        # Create a tenant
        tenant = self.tenantMgr.CreateTenant(name=TENANT_NAME, description=TENANT_DESC)

        # Add privileges to the tenant
        self.tenantMgr.AddPrivilege(tenant, p1)
        self.tenantMgr.AddPrivilege(tenant, p2, default_datastore=True)

        # Get the tenant
        result = self.tenantMgr.GetTenants(name=TENANT_NAME)
        self.assertTrue(result)

        # Verify the privileges
        privileges = result[0].privileges
        self.assertTrue(privileges)
        self.assertEqual(len(privileges), 2)

        privilege1 = None
        privilege2 = None
        for privilege in privileges:
            if privilege.datastore == self.datastore:
                privilege1 = privilege
            elif privilege.datastore == self.datastore2:
                privilege2 = privilege
        self.assertTrue(privilege1)
        self.assertTrue(privilege2)

        self.assertEqual(privilege1.allow_create, True)
        self.assertEqual(privilege1.volume_max_size, 512)
        self.assertEqual(privilege1.volume_total_size, 1024)

        self.assertEqual(privilege2.allow_create, False)
        self.assertEqual(privilege2.volume_max_size, 1024)
        self.assertEqual(privilege2.volume_total_size, 2048)

        # Verify the default datastore
        self.assertEqual(result[0].default_datastore, self.datastore2)

if __name__ == "__main__":
    log_config.configure()
    unittest.main()
