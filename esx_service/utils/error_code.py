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
# limitations under the License

""" Definiton of error code and error message """
class ErrorCode:
    # Tenant related error code start
    VM_NOT_BELONG_TO_TENANT = 1
    TENANT_NOT_EXIST = 2
    TENANT_ALREADY_EXIST = 3
    TENANT_NAME_NOT_FOUND = 4
    TENANT_CREATE_FAILED = 5
    TENANT_SET_ACCESS_PRIVILEGES_FAILED = 6
    TENANT_GET_FAILED = 7
    # Tenant related error code end

    # VM related error code start
    VM_NOT_FOUND = 101
    REPLACE_VM_EMPTY = 102
    # VM related error code end

    # Privilege related error code start
    PRIVILEGE_NOT_FOUND = 201
    # Privilege related error code end

    # DATASTORE related error code start
    DEFAULT_DS_NOT_SET = 301
    # DATASTORE related error code end

    # VMODL related error code start
    VMODL_TENANT_NAME_EMPTY = 401
    VMODL_TENANT_NAME_TOO_LONG =402
    VMODL_TENANT_DESCRIPTION_TOO_LONG = 403
    # VMODL related error code end

    INTERNAL_ERROR = 501


error_codes_to_messages = {
    ErrorCode.VM_NOT_BELONG_TO_TENANT : "VM {0} does not belong to any tenant",
    ErrorCode.TENANT_NOT_EXIST : "Tenant {0} does not exist",
    ErrorCode.TENANT_ALREADY_EXIST : "Tenant {0} already exists",
    ErrorCode.TENANT_NAME_NOT_FOUND : "Cannot find tenant name for tenant with {0}",
    ErrorCode.TENANT_CREATE_FAILED : "Tenant {0} create failed with err: {1}",
    ErrorCode.TENANT_SET_ACCESS_PRIVILEGES_FAILED : "Tenant {0} set access privileges on datastore {1} failed with err: {2}",
    ErrorCode.TENANT_GET_FAILED : "Get Tenant {0} failed",

    ErrorCode.VM_NOT_FOUND : "Cannot find vm {0}",
    ErrorCode.REPLACE_VM_EMPTY : "Replace VM cannot be empty",

    ErrorCode.PRIVILEGE_NOT_FOUND : "No privilege exists for ({0}, {1})",

    ErrorCode.DEFAULT_DS_NOT_SET : "Default datastore is not set",

    ErrorCode.VMODL_TENANT_NAME_EMPTY : "Tenant name {0} is empty",
    ErrorCode.VMODL_TENANT_NAME_TOO_LONG : "Tenant name {0} exceeds 64 characters",
    ErrorCode.VMODL_TENANT_DESCRIPTION_TOO_LONG : "Tenant description {0} exceeds 256 characters",

    ErrorCode.INTERNAL_ERROR : "Internal Error({0})"
}

class ErrorInfo:
    """ A class to abstract ErrorInfo object
        @Param code: error_code
        @Param msg: detailed error message
    """

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
