#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell OpenManage Ansible Modules
# Version 9.9.0
# Copyright (C) 2024 Dell Inc. or its subsidiaries. All Rights Reserved.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r"""
---
module: omevv_baseline_profile
short_description: Create, modify, or delete baseline profile
version_added: "9.9.0"
description: This module allows you to create, modify, or delete an OpenManage Enterprise Integration for VMware Center (OMEVV) baseline profile.
extends_documentation_fragment:
  - dellemc.openmanage.omevv_auth_options
options:
  state:
    description:
      - C(present) creates an OMEVV baseline profile or modifies an existing profile if the profile with the same name already exists.
      - C(absent) deletes the OMEVV baseline profile.
      - I(repository_profile), I(cluster), I(days) and I(time) is required when creating a new baseline profile.
      - Either I(profile_name) or I(profile_id) is required when I(state) is C(absent).
    type: str
    choices: [present, absent]
    default: present
  name:
    description:
      - Name of the OMEVV baseline profile.
      - This parameter is required for modification operation when I(state) is C(absent).
    type: str
    required: true
  description:
    description:
      - Description of OMEVV baseline profile.
    type: str
  cluster:
    description:
      - List of cluster(s) for baseline profile creation.
      - This parameter is required when I(state) is C(present) and while creating a new profile.
    type: list
    elements: str
  repository_profile:
    description:
      - Repository profile for baseline creation.
      - This is required when I(state) is C(present) and while creating a new profile.
    type: str
  days:
    description:
      - Required days of a week on when the job must run.
      - This is required when I(state) is C(present) and while creating a new profile.
    type: list
    elements: str
    choices: [sunday, monday, tuesday, wednesday, thursday, friday, saturday, all]
  time:
    description:
      - Time at when the job must run, and is 24 hours format.
      - The format must be HH:MM.
      - This is required when I(state) is C(present) and while creating a new profile.
    type: str
  job_wait:
    description: Whether to wait till completion of the job.
    type: bool
    default: true
  job_wait_timeout:
    description:
      - The maximum wait time of I(job_wait) in seconds. The job is tracked only for this duration.
      - This is applicable when I(job_wait) is C(true).
    type: int
    default: 1200
requirements:
  - "python >= 3.9.6"
author:
  - "Saksham Nautiyal (@Saksham-Nautiyal)"
attributes:
    check_mode:
        description: Runs task to validate without performing action on the target machine.
        support: full
    diff_mode:
        description: Runs the task to report the changes that are made or the changes that must be applied.
        support: full
notes:
    - Run this module from a system that has direct access to Dell OpenManage Enterprise.
"""

EXAMPLES = r"""
---
- name: Create a baseline profile for multiple cluster
  dellemc.openmanage.omevv_baseline_profile:
    hostname: "192.168.0.1"
    vcenter_uuid: "xxxxx"
    vcenter_username: "username"
    vcenter_password: "password"
    ca_path: "path/to/ca_file"
    state: "present"
    name: "profile-1"
    repository_profile: "repository-profile"
    cluster:
      - "cluster-1"
      - "cluster-2"
    days:
      - "sunday"
      - "wednesday"
    time: "22:10"

- name: Modify a baseline profile
  dellemc.openmanage.omevv_baseline_profile:
    hostname: "192.168.0.1"
    vcenter_uuid: "xxxxx"
    vcenter_username: "username"
    vcenter_password: "password"
    ca_path: "path/to/ca_file"
    state: "present"
    name: "profile-1"
    new_name: "profile-newname"
    repository_profile: "repository-profile"
    cluster:
      - "cluster-1"
      - "cluster-2"
    days:
      - "sunday"
    time: "05:00"

- name: Delete a specific baseline profile
  dellemc.openmanage.omevv_baseline_profile:
    hostname: "192.168.0.1"
    vcenter_uuid: "xxxxx"
    vcenter_username: "username"
    vcenter_password: "password"
    ca_path: "path/to/ca_file"
    state: "absent"
    name: "profile-1"
"""

RETURN = r'''
---
msg:
  type: str
  description: Status of the profile operation.
  returned: always
  sample: "Successfully created the OMEVV baseline profile."
error_info:
  description: Details of the HTTP Error.
  returned: on HTTP error
  type: dict
  sample:
    {
      "errorCode": "18001",
      "message": "Baseline profile with name Test already exists."
    }
'''
import json
import time
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import ConnectionError
from ansible_collections.dellemc.openmanage.plugins.module_utils.omevv import RestOMEVV, OMEVVAnsibleModule
from ansible_collections.dellemc.openmanage.plugins.module_utils.utils import validate_job_wait, validate_time
from ansible_collections.dellemc.openmanage.plugins.module_utils.omevv_utils.omevv_firmware_utils import OMEVVFirmwareProfile, OMEVVBaselineProfile


SUCCESS_CREATION_MSG = "Successfully created the baseline profile."
FAILED_CREATION_MSG = "Unable to create the baseline profile."
SUCCESS_MODIFY_MSG = "Successfully modified the baseline profile."
FAILED_MODIFY_MSG = "Unable to modify the baseline profile."
SUCCESS_DELETION_MSG = "Successfully deleted the baseline profile."
FAILED_DELETION_MSG = "Unable to delete the baseline profile."
PROFILE_NOT_FOUND_MSG = "Unable to delete the profile {profile_name} because the profile name is invalid. Enter a valid profile name and retry the operation."
CHANGES_FOUND_MSG = "Changes found to be applied."
CHANGES_NOT_FOUND_MSG = "No changes found to be applied."
TIMEOUT_NEGATIVE_OR_ZERO_MSG = "The value for the 'job_wait_timeout' parameter cannot be negative or zero."
INVALID_TIME_FORMAT_MSG = "Invalid value for time. Enter the value in positive integer."


class BaselineProfile:

    def __init__(self, module, rest_obj):
        self.module = module
        self.obj = rest_obj
        self.omevv_baseline_obj = OMEVVBaselineProfile(self.obj)
        self.omevv_profile_obj = OMEVVFirmwareProfile(self.obj)

    def validate_common_params(self):
        resp = validate_job_wait(self.module)
        if resp:
            self.module.exit_json(msg=TIMEOUT_NEGATIVE_OR_ZERO_MSG, failed=True)
        validate_time(self.module.params.get('time'), self.module)

        repository_profile = self.module.params.get('repository_profile')
        repo_validation = self.omevv_baseline_obj.validate_repository_profile(repository_profile)
        if "error" in repo_validation:
            self.module.exit_json(msg=repo_validation["error"], failed=True)

        cluster_names = self.module.params.get('cluster')
        vcenter_uuid = self.module.params.get('vcenter_uuid')
        cluster_validation = self.omevv_baseline_obj.validate_cluster_names(cluster_names, vcenter_uuid)
        if "error" in cluster_validation:
            self.module.exit_json(msg=cluster_validation["error"], failed=True)

    def execute(self):
        """To be overridden by subclasses to implement specific profile creation or deletion logic."""
        pass


class CreateBaselineProfile(BaselineProfile):

    def __init__(self, module, rest_obj, existing_profile=None):
        super().__init__(module, rest_obj)
        self.existing_profile = existing_profile

    def get_cluster_groups(self, cluster_names):
        cluster_groups = []
        for cluster_name in cluster_names:
            group_id = self.omevv_baseline_obj.get_group_ids_for_clusters(
                vcenter_uuid=self.module.params.get('vcenter_uuid'),
                cluster_name=cluster_name
            )
            cluster_id = self.omevv_baseline_obj.get_cluster_id(cluster_name, vcenter_uuid=self.module.params.get('vcenter_uuid'))
            cluster_groups.append({
                "clusterID": cluster_id,
                "clusterName": cluster_name,
                "omevv_groupID": group_id
            })
        return cluster_groups

    def diff_mode_check(self, payload):
        cluster_names = self.module.params.get('cluster', [])
        vcenter_uuid = self.module.params.get('vcenter_uuid')
        description = self.module.params.get('description')
        cluster_ids = self.omevv_baseline_obj.get_cluster_id(cluster_names, vcenter_uuid)
        group_ids = self.omevv_baseline_obj.get_group_ids_for_clusters(vcenter_uuid, cluster_names)

        cluster_groups = [
            {
                "clusterID": cluster_id,
                "clusterName": cluster_name,
                "omevv_groupID": group_id
            }
            for cluster_name, cluster_id, group_id in zip(cluster_names, cluster_ids, group_ids)
        ]

        filtered_payload = {
            "name": payload.get("name"),
            "firmwareRepoId": payload.get("firmwareRepoId"),
            "firmwareRepoName": self.module.params.get('repository_profile'),
            "clusterGroups": cluster_groups,
            "description": description,
            "jobSchedule": payload.get('jobSchedule')
        }

        diff = {
            "before": {},
            "after": {k: v for k, v in filtered_payload.items() if v is not None}
        }
        return diff

    def perform_create_baseline_profile(self, payload):
        diff = {}
        vcenter_uuid = self.module.params.get('vcenter_uuid')
        response, err_msg = self.omevv_baseline_obj.create_baseline_profile(
            name=payload.get('name'),
            firmware_repo_id=payload.get('firmwareRepoId'),
            group_ids=payload.get('groupIds'),
            vcenter_uuid=vcenter_uuid,
            payload=payload
        )
        if response.success:
            profile_resp = self.omevv_baseline_obj.get_baseline_profile_by_id(response.json_data, vcenter_uuid)
            while profile_resp.json_data["status"] not in ["SUCCESSFUL", "FAILED"]:
                time.sleep(3)
                profile_resp = self.omevv_baseline_obj.get_baseline_profile_by_id(response.json_data, vcenter_uuid)

            diff = self.diff_mode_check(payload)
            if self.module._diff and profile_resp.json_data["status"] == "SUCCESSFUL":
                self.module.exit_json(msg=SUCCESS_CREATION_MSG, baseline_profile_info=profile_resp.json_data, diff=diff, changed=True)
            elif profile_resp.json_data["status"] == "SUCCESSFUL":
                self.module.exit_json(msg=SUCCESS_CREATION_MSG, baseline_profile_info=profile_resp.json_data, changed=True)
            else:
                self.module.exit_json(msg=FAILED_CREATION_MSG, baseline_profile_info=profile_resp.json_data, failed=True)
        else:
            self.module.exit_json(msg=FAILED_CREATION_MSG, failed=True)

    def execute(self):
        self.validate_common_params()
        firmware_repo_id = self.omevv_baseline_obj.get_repo_id_by_name(self.module.params.get('repository_profile'))
        group_ids = self.omevv_baseline_obj.get_group_ids_for_clusters(
            vcenter_uuid=self.module.params.get('vcenter_uuid'),
            cluster_names=self.module.params.get('cluster')
        )
        job_schedule = self.omevv_baseline_obj.create_job_schedule(self.module.params.get('days'), self.module.params.get('time'))
        payload = {
            "name": self.module.params.get('name'),
            "firmwareRepoId": firmware_repo_id,
            "groupIds": group_ids
        }

        description = self.module.params.get('description')
        if description is not None:
            payload["description"] = description
        if job_schedule:
            payload["jobSchedule"] = job_schedule

        if self.module.check_mode and self.module._diff:
            diff = self.diff_mode_check(payload)
            self.module.exit_json(msg=CHANGES_FOUND_MSG, diff=diff, changed=True)

        if self.module.check_mode:
            self.module.exit_json(msg=CHANGES_FOUND_MSG, changed=True)

        self.create_baseline_profile(payload)


class ModifyBaselineProfile(BaselineProfile):

    def __init__(self, module, rest_obj, existing_profile):
        super().__init__(module, rest_obj)
        self.existing_profile = existing_profile

    def diff_mode_check(self, payload):
        cluster_names = self.module.params.get('cluster', [])
        vcenter_uuid = self.module.params.get('vcenter_uuid')
        description = self.module.params.get('description', self.existing_profile.get("description"))

        # Fetch cluster and group IDs for new clusters
        cluster_ids = self.omevv_baseline_obj.get_cluster_id(cluster_names, vcenter_uuid)
        group_ids = self.omevv_baseline_obj.get_group_ids_for_clusters(vcenter_uuid, cluster_names)
        cluster_groups = [
            {
                "clusterID": cluster_id,
                "clusterName": cluster_name,
                "omevv_groupID": group_id
            }
            for cluster_name, cluster_id, group_id in zip(cluster_names, cluster_ids, group_ids)
        ]

        # Retrieve job_schedule from drift API call
        old_job_schedule_resp = self.omevv_baseline_obj.get_current_job_schedule(self.existing_profile.get("driftJobId"), vcenter_uuid)
        old_job_schedule = old_job_schedule_resp.json_data.get("schedule")

        new_job_schedule = payload['jobSchedule']

        # Construct the 'after' payload for comparison
        modified_payload = {
            "name": self.module.params.get("name"),
            "firmwareRepoId": payload.get("firmwareRepoId"),
            "firmwareRepoName": self.module.params.get('repository_profile'),
            "clusterGroups": cluster_groups,
            "description": description,
            "jobSchedule": new_job_schedule
        }
        filtered_existing_profile = {
            k: v for k, v in self.existing_profile.items() if k in modified_payload
        }
        filtered_existing_profile["jobSchedule"] = old_job_schedule

        if filtered_existing_profile == modified_payload:
            return {"before": {}, "after": {}}
        else:
            return {
                "before": {k: v for k, v in filtered_existing_profile.items() if v is not None},
                "after": {k: v for k, v in modified_payload.items() if v is not None}
            }

    def perform_modify_baseline_profile(self, payload, diff_before_modify):
        diff = diff_before_modify
        profile_id = self.existing_profile.get('id')
        vcenter_uuid = self.module.params.get('vcenter_uuid')

        response, err_msg = self.omevv_baseline_obj.modify_baseline_profile(profile_id, vcenter_uuid, payload)
        if response.success:
            profile_resp = self.omevv_baseline_obj.get_baseline_profile_by_id(profile_id, vcenter_uuid)
            while profile_resp.json_data["status"] not in ["SUCCESSFUL", "FAILED"]:
                time.sleep(3)
                profile_resp = self.omevv_baseline_obj.get_baseline_profile_by_id(profile_id, vcenter_uuid)

            if self.module._diff and profile_resp.json_data["status"] == "SUCCESSFUL":
                self.module.exit_json(msg=SUCCESS_MODIFY_MSG, baseline_profile_info=profile_resp.json_data, diff=diff, changed=True)
            elif profile_resp.json_data["status"] == "SUCCESSFUL":
                self.module.exit_json(msg=SUCCESS_MODIFY_MSG, baseline_profile_info=profile_resp.json_data, changed=True)
            else:
                self.module.exit_json(msg=FAILED_MODIFY_MSG, baseline_profile_info=profile_resp.json_data, failed=True)
        else:
            self.module.exit_json(msg=FAILED_MODIFY_MSG, failed=True)

    def execute(self):
        self.validate_common_params()
        add_group_ids, remove_group_ids = self.omevv_baseline_obj.get_add_remove_group_ids(
            self.existing_profile,
            self.module.params.get('vcenter_uuid'),
            self.module.params.get('cluster')
        )

        job_schedule = self.omevv_baseline_obj.create_job_schedule(
            self.module.params.get('days'),
            self.module.params.get('time')
        )

        repository_name = self.module.params.get("repository_profile")
        firmware_repo_id = self.omevv_baseline_obj.get_repo_id_by_name(repository_name)

        # Prepare the new payload
        new_payload = {
            "addgroupIds": add_group_ids,
            "removeGroupIds": remove_group_ids,
            "jobSchedule": job_schedule,
            "description": self.module.params.get("description", self.existing_profile.get("description")),
            "configurationRepoId": self.module.params.get("configurationRepoId", 0),
            "firmwareRepoId": firmware_repo_id,
            "driverRepoId": self.module.params.get("driverRepoId", 0),
            "modifiedBy": "Administrator@VSPHERE.LOCAL"
        }

        diff = self.diff_mode_check(new_payload)
        if not diff["before"] and not diff["after"]:
            self.module.exit_json(msg=CHANGES_NOT_FOUND_MSG, changed=False)

        if self.module.check_mode and self.module._diff:
            self.module.exit_json(msg=CHANGES_FOUND_MSG, diff=diff, changed=True)

        if self.module.check_mode:
            self.module.exit_json(msg=CHANGES_FOUND_MSG, changed=True)

        self.modify_baseline_profile(new_payload, diff)


class DeleteBaselineProfile(BaselineProfile):

    def __init__(self, module, rest_obj, profile_name):
        super().__init__(module, rest_obj)
        self.profile_name = profile_name

    def diff_mode_check(self, payload):
        diff = {}
        diff_dict = {}
        diff_dict["name"] = payload["name"]
        diff_dict["description"] = payload["description"]
        diff_dict["firmwareRepoId"] = payload["firmwareRepoId"]
        diff_dict["firmwareRepoName"] = payload["firmwareRepoName"]
        diff_dict["clusterGroups"] = payload["clusterGroups"]
        if self.module._diff:
            diff = dict(
                before=diff_dict,
                after={}
            )
        return diff

    def perform_delete_baseline_profile(self, profile_resp):
        diff = {}
        diff = self.diff_mode_check(profile_resp)
        vcenter_uuid = self.module.params.get('vcenter_uuid')
        resp = self.omevv_baseline_obj.delete_baseline_profile(profile_resp["id"], vcenter_uuid)
        if resp.success:
            if self.module._diff:
                self.module.exit_json(msg=SUCCESS_DELETION_MSG, baseline_profile_info={}, diff=diff, changed=True)
            self.module.exit_json(msg=SUCCESS_DELETION_MSG, baseline_profile_info={}, changed=True)
        else:
            self.module.exit_json(msg=FAILED_DELETION_MSG, failed=True)

    def execute(self):
        vcenter_uuid = self.module.params.get('vcenter_uuid')
        profile_exists = self.omevv_baseline_obj.get_baseline_profile_by_name(self.profile_name, vcenter_uuid)
        profile = self.module.params.get('name')

        if profile_exists and self.module.check_mode and self.module._diff:
            diff = self.diff_mode_check(profile_exists)
            self.module.exit_json(msg=CHANGES_FOUND_MSG, diff=diff, changed=True)
        if not profile_exists and self.module.check_mode:
            self.module.exit_json(msg=CHANGES_NOT_FOUND_MSG, changed=False)
        if not profile_exists and not self.module.check_mode and self.module._diff:
            self.module.exit_json(msg=CHANGES_NOT_FOUND_MSG, diff={"before": {}, "after": {}}, changed=False)
        if not profile_exists and not self.module.check_mode:
            self.module.exit_json(msg=CHANGES_NOT_FOUND_MSG, changed=False)
        if profile_exists and not self.module.check_mode:
            self.delete_baseline_profile(profile_exists)
        if profile_exists and self.module.check_mode:
            self.module.exit_json(msg=CHANGES_FOUND_MSG, changed=True)


def main():
    argument_spec = {
        "state": {"type": 'str', "choices": ['present', 'absent'], "default": 'present'},
        "name": {"required": True, "type": 'str'},
        "cluster": {"type": 'list', "elements": 'str'},
        "description": {"type": 'str'},
        "days": {
            "type": 'list', "elements": 'str',
            "choices": ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'all']
        },
        "time": {
            "type": 'str', "required": False
        },
        "repository_profile": {"type": 'str'},
        "job_wait": {"type": 'bool', "default": True},
        "job_wait_timeout": {"type": 'int', "default": 1200}
    }
    module = OMEVVAnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ["state", "present", ["repository_profile", "cluster", "days", "time"]],
            ["state", "absent", ["name"]]
        ],        supports_check_mode=True

    )
    try:
        with RestOMEVV(module.params) as rest_obj:
            profile_name = module.params.get('name')
            vcenter_uuid = module.params.get('vcenter_uuid')
            omevv_baseline_profile = OMEVVBaselineProfile(rest_obj)
            if module.params.get('state') == 'present':
                existing_profile = omevv_baseline_profile.get_baseline_profile_by_name(profile_name, vcenter_uuid)

                if existing_profile:
                    omevv_obj = ModifyBaselineProfile(module, rest_obj, existing_profile)
                else:
                    omevv_obj = CreateBaselineProfile(module, rest_obj, existing_profile)

            elif module.params.get('state') == 'absent':
                omevv_obj = DeleteBaselineProfile(module, rest_obj, profile_name)
            
            omevv_obj.execute()

    except HTTPError as err:
        if err.code == 500:
            module.exit_json(msg=json.load(err), failed=True)
        error_info = json.load(err)
        code = error_info.get('errorCode')
        message = error_info.get('message')
        if '18001' in code and module.check_mode:
            module.exit_json(msg=CHANGES_NOT_FOUND_MSG)
        if '500' in code:
            module.exit_json(msg=message, skipped=True)
        module.exit_json(msg=message, error_info=error_info, failed=True)
    except URLError as err:
        module.exit_json(msg=str(err), unreachable=True)
    except (IOError, ValueError, TypeError, ConnectionError,
            AttributeError, IndexError, KeyError, OSError) as err:
        module.exit_json(msg=str(err), failed=True)


if __name__ == '__main__':
    main()
