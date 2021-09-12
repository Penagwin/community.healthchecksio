#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: checks
short_description: Create, delete, update, pause checks
description:
  - Create, delete, update, pause checks
author: "Mark Mercado (@mamercad)"
version_added: 0.1.0
options:
  # api_token:
  #   aliases: ["api_key"]
  #   description:
  #     - Healthchecks.io API token.
  #     - There are several environment variables which can be used to provide this value:
  #     - C(HEALTHCHECKSIO_API_TOKEN), C(HEALTHCHECKSIO_API_KEY), C(HC_API_TOKEN), C(HC_API_KEY)
  #   type: str
  #   required: true
  state:
    description:
      - C(present) will create or update a check.
      - C(absent) will delete a check.
      - C(pause) will pause a check.
    type: str
    choices: ["present", "absent", "pause"]
    default: present
  name:
    description:
      - Name for the new check.
    type: str
    required: false
    default: ""
  tags:
    description:
      - Tags for the check.
    type: list
    elements: str
    required: false
    default: []
  desc:
    description:
      - Description of the check.
    type: str
    required: false
    default: ""
  timeout:
    description:
      - A number of seconds, the expected period of this check.
      - Minimum 60 (one minute), maximum 2592000 (30 days).
    type: int
    required: false
    default: 86400
  grace:
    description:
      - A number of seconds, the grace period for this check.
    type: int
    required: false
    default: 3600
  schedule:
    description:
      - A cron expression defining this check's schedule.
      - If you specify both timeout and schedule parameters, Healthchecks.io will create a Cron check and ignore the timeout value.
    type: str
    required: false
    default: "* * * * *"
  tz:
    description:
      - Server's timezone. This setting only has an effect in combination with the schedule parameter.
    type: str
    required: false
    default: UTC
  manual_resume:
    description:
      - Controls whether a paused check automatically resumes when pinged (the default) or not.
      - If set to false, a paused check will leave the paused state when it receives a ping.
      - If set to true, a paused check will ignore pings and stay paused until you manually resume it from the web dashboard.
    type: bool
    required: false
    default: false
  methods:
    description:
      - Specifies the allowed HTTP methods for making ping requests.
      - Must be one of the two values "" (an empty string) or "POST".
      - Set this field to "" (an empty string) to allow HEAD, GET, and POST requests.
      - Set this field to "POST" to allow only POST requests.
    type: str
    required: false
    default: ""
  channels:
    description:
      - By default, this API call assigns no integrations to the newly created check.
      - Set this field to a special value "*" to automatically assign all existing integrations.
      - To assign specific integrations, use a comma-separated list of integration UUIDs.
    type: str
    required: false
    default: ""
  unique:
    description:
      - Enables "upsert" functionality.
      - Before creating a check, Healthchecks.io looks for existing checks, filtered by fields listed in unique.
      - The accepted values for the unique field are C(name), C(tags), C(timeout), and C(grace).
    type: list
    elements: str
    required: false
    default: []
  uuid:
    description:
      - Check uuid to delete when state is C(absent) or C(pause).
    type: str
    required: false
    default: ""
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
"""

RETURN = r"""
"""

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
)
from ansible.module_utils.basic import AnsibleModule, env_fallback


class Checks(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)
        self.api_token = module.params.pop("api_token")

    def create(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        endpoint = "checks/"

        request_params = dict(self.module.params)

        # uuid is not used to create or update, pop it
        del request_params["uuid"]

        tags = self.module.params.get("tags", [])
        request_params["tags"] = " ".join(tags)

        response = self.rest.post(endpoint, data=request_params)
        json_data = response.json
        status_code = response.status_code

        # determine the uuid
        uuid = json_data.get("ping_url").split("/")[3]

        if status_code == 200:
            self.module.exit_json(
                changed=True,
                msg="Existing check {0} found and updated".format(uuid),
                data=json_data,
            )

        elif status_code == 201:
            self.module.exit_json(
                changed=True,
                msg="New check {0} created".format(uuid),
                data=json_data,
            )

        else:
            self.module.fail_json(
                changed=False,
                msg="Failed to create or update delete check [HTTP {0}]".format(status_code),
            )

        self.module.exit_json(changed=True, data=json_data)

    def delete(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        uuid = self.module.params.get("uuid")
        endpoint = "checks/{0}".format(uuid)
        response = self.rest.delete(endpoint)
        status_code = response.status_code

        if status_code == 200:
            self.module.exit_json(
                changed=True,
                msg="Check {0} successfully deleted".format(uuid),
            )
        elif status_code == 404:
            self.module.exit_json(
                changed=False,
                msg="Check {0} not found".format(uuid),
            )
        else:
            self.module.fail_json(
                changed=False,
                msg="Failed delete check {0} [HTTP {1}]".format(
                    uuid,
                    status_code,
                ),
            )

    def pause(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        uuid = self.module.params.get("uuid")
        endpoint = "checks/{0}/pause".format(uuid)
        response = self.rest.post(endpoint)
        status_code = response.status_code

        if status_code == 200:
            self.module.exit_json(
                changed=True,
                msg="Check {0} successfully paused".format(uuid),
            )
        elif status_code == 404:
            self.module.exit_json(
                changed=False,
                msg="Check {0} not found".format(uuid),
            )
        else:
            self.module.fail_json(
                changed=False,
                msg="Failed delete check {0} [HTTP {1}]".format(
                    uuid,
                    status_code,
                ),
            )


def run(module):
    state = module.params.pop("state")
    checks = Checks(module)
    if state == "present":
        checks.create()
    elif state == "absent":
        checks.delete()
    elif state == "pause":
        checks.pause()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(
        state=dict(
            type="str",
            choices=["present", "absent", "pause"],
            default="present",
        ),
        name=dict(type="str", required=False, default=""),
        tags=dict(type="list", elements="str", required=False, default=[]),
        desc=dict(type="str", required=False, default=""),
        timeout=dict(type="int", required=False, default=86400),
        grace=dict(type="int", required=False, default=3600),
        schedule=dict(type="str", required=False, default="* * * * *"),
        tz=dict(type="str", required=False, default="UTC"),
        manual_resume=dict(type="bool", required=False, default=False),
        methods=dict(type="str", required=False, default=""),
        channels=dict(type="str", required=False, default=""),
        unique=dict(type="list", elements="str", required=False, default=[]),
        uuid=dict(type="str", required=False, default=""),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["uuid"]),
            ("state", "pause", ["uuid"]),
        ],
    )

    run(module)


if __name__ == "__main__":
    main()