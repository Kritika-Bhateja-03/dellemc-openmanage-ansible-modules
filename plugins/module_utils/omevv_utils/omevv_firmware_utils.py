# -*- coding: utf-8 -*-

# Dell OpenManage Ansible Modules
# Version 9.8.0
# Copyright (C) 2024 Dell Inc. or its subsidiaries. All Rights Reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:

#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#


from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

INVALID_REPO_PROFILE_MSG = "Invalid repository profile: {repository_profile}. Please provide a valid profile."
NO_REPO_PROFILE_MSG = "No repository profiles found."
INVALID_CLUSTER_NAMES_MSG = "Invalid cluster names: {cluster_names}. Please provide valid clusters."
NO_CLUSTERS_FOUND_MSG = "No clusters found."
PROFILE_URI = "/RepositoryProfiles"
TEST_CONNECTION_URI = "/RepositoryProfiles/TestConnection"
BASELINE_PROFILE_URI = "/Consoles/{vcenter_uuid}/BaselineProfiles"
TEST_CONNECTION_URI = "/RepositoryProfiles/TestConnection"
CLUSTER_URI = "/Consoles/{vcenter_uuid}/Clusters"
CLUSTER_IDS_URI = "/Consoles/{vcenter_uuid}/Groups/getGroupsForClusters"
DRIFT_URI = "/Consoles/{vcenter_uuid}/UpdateJobs"


class OMEVVFirmwareProfile:
    def __init__(self, omevv):
        self.omevv = omevv

    def get_firmware_repository_profile(self, profile_name=None):
        """
        Retrieves the firmware repository profile information.

        Args:
            profile_name (str, optional): The name of the profile to search for. Defaults to None.

        Returns:
            list: The list of firmware repository profile information.
        """
        resp = self.omevv.invoke_request('GET', PROFILE_URI)
        profile_info = []
        if resp.success:
            profile_info = resp.json_data
            if profile_name:
                profile_info = self.search_profile_name(profile_info, profile_name)
        return profile_info

    def get_all_repository_profiles(self):
        """
        Retrieves the firmware repository profile information.

        Returns:
            list: The list of all firmware repository profile information.
        """
        resp = self.omevv.invoke_request('GET', PROFILE_URI)

        return resp

    def get_create_payload_details(self, name, catalog_path, description, protocol_type, share_username, share_password, share_domain):
        """
        Returns a dictionary containing the payload details for creating a firmware repository profile.

        Args:
            name (str): The name of the firmware repository profile.
            catalog_path (str): The path to the firmware catalog.
            description (str, optional): The description of the firmware repository profile.
            protocol_type (str): The protocol type of the firmware repository profile.
            share_username (str): The username for the share credential.
            share_password (str): The password for the share credential.
            share_domain (str): The domain for the share credential.

        Returns:
            dict: A dictionary containing the payload details for creating a firmware repository profile.
        """
        payload = {}
        payload["profileName"] = name
        payload["protocolType"] = protocol_type
        payload["sharePath"] = catalog_path
        if description is not None:
            payload["description"] = description
        payload["profileType"] = "Firmware"
        payload["shareCredential"] = {
            "username": share_username,
            "password": share_password,
            "domain": share_domain
        }
        return payload

    def get_modify_payload_details(self, name, catalog_path, description, share_username, share_password, share_domain):
        """
        Returns a dictionary containing the payload details for modifying a firmware repository profile.

        Args:
            name (str): The name of the firmware repository profile.
            catalog_path (str): The path to the firmware catalog.
            description (str, optional): The description of the firmware repository profile.
            share_username (str): The username for the share credential.
            share_password (str): The password for the share credential.
            share_domain (str): The domain for the share credential.

        Returns:
            dict: A dictionary containing the payload details for modifying a firmware repository profile.
        """
        payload = {}
        payload["profileName"] = name
        payload["sharePath"] = catalog_path
        if description is not None:
            payload["description"] = description
        payload["shareCredential"] = {
            "username": share_username,
            "password": share_password,
            "domain": share_domain
        }
        return payload

    def form_conn_payload(self, protocol_type, catalog_path, share_username, share_password, share_domain):
        """
        Returns a dictionary containing the payload details for testing the connection to a firmware repository.

        Args:
            protocol_type (str): The protocol type of the firmware repository.
            catalog_path (str): The path to the firmware catalog.
            share_username (str): The username for the share credential.
            share_password (str): The password for the share credential.
            share_domain (str): The domain for the share credential.

        Returns:
            dict: A dictionary containing the payload details for testing the connection to a firmware repository.
        """
        payload = {}
        payload["protocolType"] = protocol_type
        payload["catalogPath"] = catalog_path
        payload["shareCredential"] = {
            "username": share_username if share_username is not None else "",
            "password": share_password if share_password is not None else "",
            "domain": share_domain if share_domain is not None else ""
        }
        payload["checkCertificate"] = False
        return payload

    def search_profile_name(self, data, profile_name):
        """
        Searches for a profile with the given name in the provided data.

        Args:
            data (list): A list of dictionaries representing profiles.
            profile_name (str): The name of the profile to search for.

        Returns:
            dict: The dictionary representing the profile if found, or an empty dictionary if not found.
        """
        for d in data:
            if d.get('profileName') == profile_name:
                return d
        return {}

    def test_connection(self, protocol_type, catalog_path, share_username, share_password, share_domain):
        """
        Tests the connection to the vCenter server.

        """
        payload = self.form_conn_payload(
            protocol_type, catalog_path, share_username, share_password, share_domain)
        resp = self.omevv.invoke_request("POST", TEST_CONNECTION_URI, payload)
        return resp

    def get_firmware_repository_profile_by_id(self, profile_id):
        """
        Retrieves all firmware repository profile Information.

        """
        resp = self.omevv.invoke_request(
            "GET", PROFILE_URI + "/" + str(profile_id))
        return resp

    def create_firmware_repository_profile(self, name, catalog_path,
                                           description, protocol_type,
                                           share_username, share_password,
                                           share_domain):
        """
        Creates a firmware repository profile.

        Args:
            name (str): The name of the firmware repository profile.
            catalog_path (str): The path to the firmware catalog.
            description (str, optional): The description of the firmware repository profile.
            protocol_type (str): The protocol type of the firmware repository profile.
            share_username (str): The username for the share credential.
            share_password (str): The password for the share credential.
            share_domain (str): The domain for the share credential.

        Returns:
            tuple: A tuple containing the response and an error message.

        Raises:
            None.

        """
        err_msg = None
        required_params = [name, catalog_path, protocol_type]
        missing_params = [param for param in required_params if param is None]
        if missing_params:
            err_msg = "Required parameters such as: " + ", ".join(missing_params)

        payload = self.get_create_payload_details(name, catalog_path,
                                                  description, protocol_type,
                                                  share_username, share_password,
                                                  share_domain)
        resp = self.omevv.invoke_request("POST", PROFILE_URI, payload)
        return resp, err_msg

    def modify_firmware_repository_profile(self, profile_id, name, catalog_path,
                                           description,
                                           share_username, share_password,
                                           share_domain):
        """
        Modifies a firmware repository profile.

        Args:
            profile_id (int): The ID of the firmware repository profile.
            name (str): The new name of the firmware repository profile.
            catalog_path (str): The new path to the firmware catalog.
            description (str, optional): The new description of the firmware repository profile.
            share_username (str): The new username for the share credential.
            share_password (str): The new password for the share credential.
            share_domain (str): The new domain for the share credential.

        Returns:
            tuple: A tuple containing the response and an error message.

        Raises:
            None.

        """
        err_msg = None
        required_params = [name, catalog_path]
        missing_params = [param for param in required_params if param is None]
        if missing_params:
            err_msg = "Required parameters such as: " + ", ".join(missing_params)

        payload = self.get_modify_payload_details(name, catalog_path,
                                                  description,
                                                  share_username, share_password,
                                                  share_domain)
        resp = self.omevv.invoke_request(
            "PUT", PROFILE_URI + "/" + str(profile_id), payload)
        return resp, err_msg

    def delete_firmware_repository_profile(self, profile_id):
        """
        Deletes a firmware repository profile.

        """
        resp = self.omevv.invoke_request(
            "DELETE", PROFILE_URI + "/" + str(profile_id))
        return resp


class OMEVVBaselineProfile:
    def __init__(self, omevv):
        self.omevv = omevv
        self.omevv_profile_obj = OMEVVFirmwareProfile(self.omevv)

    def validate_repository_profile(self, repository_profile, module):
        # Fetch the list of available repository profiles or check via API
        available_repo_profiles = self.omevv_profile_obj.get_all_repository_profiles()

        if not available_repo_profiles:
            return {"error": NO_REPO_PROFILE_MSG}

        available_repo_profile_names = [profile.get('profileName') for profile in available_repo_profiles.json_data]

        if repository_profile not in available_repo_profile_names:
            return {"error": INVALID_REPO_PROFILE_MSG.format(repository_profile=repository_profile)}

        return {"success": True}

    def validate_cluster_names(self, cluster_names, vcenter_uuid):
        """
        Validates the provided cluster names against the available clusters.

        Args:
            cluster_names (list): List of cluster names to validate.
            module: The Ansible module instance for logging and exiting.
        """

        available_clusters = self.get_all_clusters(vcenter_uuid)

        if not available_clusters:
            return {"error": NO_CLUSTERS_FOUND_MSG}

        available_cluster_names = [cluster.get('name') for cluster in available_clusters.json_data]
        invalid_clusters = [cluster for cluster in cluster_names if cluster not in available_cluster_names]

        if invalid_clusters:
            return {"error": INVALID_CLUSTER_NAMES_MSG.format(cluster_names=', '.join(invalid_clusters))}

        return {"success": True}

    def get_all_clusters(self, vcenter_uuid):
        """
        Retrieves the cluster information.

        Args:
            vcenter_uuid: UUID of the vCenter.

        Returns:
            list: The list of all cluster information.
        """

        resp = self.omevv.invoke_request('GET', CLUSTER_URI.format(vcenter_uuid=vcenter_uuid))
        return resp

    def get_cluster_id(self, cluster_names, vcenter_uuid):
        """
        Fetch cluster IDs for the given clusters.

        Args:
            vcenter_uuid: UUID of the vCenter.
            cluster_names: List of cluster names to fetch group IDs for.

        Returns:
            list: A list of cluster IDs.
        """
        clusters_resp = self.omevv.invoke_request('GET', CLUSTER_URI.format(vcenter_uuid=vcenter_uuid))
        clusters = clusters_resp.json_data if clusters_resp.success else []

        # Map cluster name to entity ID (clustId)
        cluster_ids = [c['entityId'] for c in clusters if c['name'] in cluster_names]

        return cluster_ids

    def get_group_ids_for_clusters(self, vcenter_uuid, cluster_names):

        """
        Fetch group IDs for the given clusters.

        Args:
            vcenter_uuid: UUID of the vCenter.
            cluster_names: List of cluster names to fetch group IDs for.

        Returns:
            list: A list of group IDs.
        """
        clusters_resp = self.omevv.invoke_request('GET', CLUSTER_URI.format(vcenter_uuid=vcenter_uuid))
        clusters = clusters_resp.json_data if clusters_resp.success else []

        # Map cluster name to entity ID (clustId)
        cluster_ids = [c['entityId'] for c in clusters if c['name'] in cluster_names]

        # Fetch group IDs for the identified cluster IDs
        group_ids = []
        if cluster_ids:
            payload = {"clustIds": cluster_ids}
            group_resp = self.omevv.invoke_request('POST', CLUSTER_IDS_URI.format(vcenter_uuid=vcenter_uuid), payload)
            group_ids = [g['groupId'] for g in group_resp.json_data] if group_resp.success else []

        return group_ids

    def get_repo_id_by_name(self, repository_profile):
        repo_profile_info = self.omevv_profile_obj.get_firmware_repository_profile(
            profile_name=repository_profile
        )

        firmware_repo_id = None
        if repo_profile_info:
            firmware_repo_id = repo_profile_info.get("id")
        return firmware_repo_id

    def get_baseline_profiles(self, vcenter_uuid):
        """
        Retrieves the list of baseline profiles associated with a given vCenter.

        Args:
            vcenter_uuid (str): The UUID of the vCenter server.

        Returns:
            list: A list of baseline profiles.

        Raises:
            None
        """
        response = self.omevv.invoke_request('GET', BASELINE_PROFILE_URI.format(vcenter_uuid=vcenter_uuid))
        if response.success:
            return response.json_data

        return []

    def get_baseline_profile_by_id(self, profile_id, vcenter_uuid):
        """
        Retrieves all baseline profile Information.

        """
        resp = self.omevv.invoke_request(
            "GET", BASELINE_PROFILE_URI.format(vcenter_uuid=vcenter_uuid) + "/" + str(profile_id))
        return resp

    def get_baseline_profile_by_name(self, profile_name, vcenter_uuid):
        """
        Retrieves all baseline profile information and checks for a profile with the given name.

        Args:
            profile_name (str): The name of the profile to search for.
            vcenter_uuid (str): The UUID of the vCenter to retrieve profiles from.

        Returns:
            dict: The dictionary representing the profile if found, or an empty dictionary if not found.
        """
        profiles = self.get_baseline_profiles(vcenter_uuid)

        for profile in profiles:
            if profile.get('name') == profile_name:
                return profile

        return {}

    def create_job_schedule(self, days, time):
        """
        Creates a job schedule based on provided days and time.

        Args:
            days (list): List of days selected for the job schedule.
            time (str): The time to be set for the job schedule.

        Returns:
            dict: A dictionary representing the job schedule.
        """
        if days and time:
            days_selected = set(days)

            if "all" in days_selected:
                return {
                    "monday": True,
                    "tuesday": True,
                    "wednesday": True,
                    "thursday": True,
                    "friday": True,
                    "saturday": True,
                    "sunday": True,
                    "time": time
                }
            else:
                return {
                    "monday": "monday" in days_selected,
                    "tuesday": "tuesday" in days_selected,
                    "wednesday": "wednesday" in days_selected,
                    "thursday": "thursday" in days_selected,
                    "friday": "friday" in days_selected,
                    "saturday": "saturday" in days_selected,
                    "sunday": "sunday" in days_selected,
                    "time": time
                }
        return None

    def get_current_job_schedule(self, profile_id, vcenter_uuid):
        """
        Retrieves the current job schedule for a baseline profile.

        Args:
            profile_id (str): The ID of the profile for which to retrieve the schedule.
            vcenter_uuid (str): The UUID of the vCenter.

        Returns:
            dict: Job schedule details if available.
        """
        resp = self.omevv.invoke_request(
            "GET", DRIFT_URI.format(vcenter_uuid=vcenter_uuid) + "/" + str(profile_id)
        )
        return resp

    def get_add_remove_group_ids(self, existing_profile, vcenter_uuid, cluster_names):
        """Determine groups to add or remove based on the cluster names"""
        current_group_ids = {group['omevv_groupID'] for group in existing_profile.get('clusterGroups', [])}

        new_group_ids = set(self.get_group_ids_for_clusters(
            vcenter_uuid=vcenter_uuid,
            cluster_names=cluster_names
        ))

        # Determine the groups that need to be added or removed
        add_group_ids = list(new_group_ids - current_group_ids)
        remove_group_ids = list(current_group_ids - new_group_ids)

        return add_group_ids, remove_group_ids

    def create_baseline_profile(self, name, firmware_repo_id, group_ids, vcenter_uuid, payload):
        """
        Creates a baseline profile.

        Args:
            name (str): The name of the baseline profile.
            firmware_repo_id (str): The ID of the firmware repository to associate with the baseline profile.
            group_ids (list): List of group IDs (clusters) associated with the baseline profile.
            description (str, optional): A description of the baseline profile.
            job_schedule (dict, optional): A dictionary specifying the job schedule details, including selected days and time.

        Returns:
            tuple: A tuple containing the response and an error message.

        Raises:
            None.
        """
        err_msg = None
        if not name or not firmware_repo_id or not group_ids:
            err_msg = "Required parameters: name, firmware_repo_id, or group_ids are missing."

        resp = self.omevv.invoke_request("POST", BASELINE_PROFILE_URI.format(vcenter_uuid=vcenter_uuid), payload)
        return resp, err_msg

    def modify_baseline_profile(self, profile_id, vcenter_uuid, payload):
        """
        Modifies an existing baseline profile.

        Args:
            profile_id (str): The ID of the baseline profile to modify.
            vcenter_uuid (str): The UUID of the vCenter environment.
            payload (dict): A dictionary containing the fields to modify in the baseline profile.

        Returns:
            tuple: A tuple containing the response and an error message.

        Raises:
            None.
        """
        err_msg = None
        if not profile_id or not vcenter_uuid or not payload:
            err_msg = "Required parameters: profile_id, vcenter_uuid, or payload are missing."

        # Construct the URL for the PATCH request
        url = BASELINE_PROFILE_URI.format(vcenter_uuid=vcenter_uuid) + f"/{profile_id}"

        # Send the PATCH request using the appropriate method (e.g., self.omevv.invoke_request)
        resp = self.omevv.invoke_request("PATCH", url, payload)

        return resp, err_msg

    def delete_baseline_profile(self, profile_id, vcenter_uuid):
        """
        Deletes a baseline profile.

        """
        resp = self.omevv.invoke_request(
            "DELETE", BASELINE_PROFILE_URI.format(vcenter_uuid=vcenter_uuid) + "/" + str(profile_id))
        return resp
