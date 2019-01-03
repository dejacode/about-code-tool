#!/usr/bin/env python
# -*- coding: utf8 -*-

# ============================================================================
#  Copyright (c) 2014-2017 nexB Inc. http://www.nexb.com/ - All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ============================================================================

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import mock

from aboutcode import api
from aboutcode import ERROR
from aboutcode import Error
from aboutcode.model import License


class FakeResponse(object):
    response_content = None

    def __init__(self, response_content):
        self.response_content = response_content

    def read(self):
        return self.response_content


class ApiTest(unittest.TestCase):

    @mock.patch.object(api, 'request_license_data')
    def test_api_get_license_details_from_api(self, request_license_data):
        license_data = {
            'name': 'Apache License 2.0',
            'full_text': 'Apache License Version 2.0 ...',
            'key': 'apache-2.0',
        }
        errors = []
        request_license_data.return_value = license_data, errors

        expected = License(
            key='apache-2.0',
            name='Apache License 2.0',
            text='Apache License Version 2.0 ...',
            url=u'http://fake.url/urn/?urn=urn:dje:license:license_key')

        result, errors = api.get_license_details(
            api_url='http://fake.url/', api_key='api_key', license_key='license_key')
        assert expected.to_dict() == result.to_dict()

    @mock.patch.object(api, 'urlopen')
    def test_api_request_license_data_with_result(self, mock_data):
        response_content = (
            b'{"count":1,"results":[{"name":"Apache 2.0","key":"apache-2.0","text":"Text"}]}'
        )
        mock_data.return_value = FakeResponse(response_content)
        license_data = api.request_license_data(
            api_url='http://fake.url/', api_key='api_key', license_key='apache-2.0')
        expected = (
            {'name': 'Apache 2.0', 'key': 'apache-2.0', 'text': 'Text'},
            []
        )
        assert expected == license_data

    @mock.patch.object(api, 'urlopen')
    def test_api_request_license_data_without_result(self, mock_data):
        response_content = b'{"count":0,"results":[]}'
        mock_data.return_value = FakeResponse(response_content)
        license_data = api.request_license_data(
            api_url='http://fake.url/', api_key='api_key', license_key='apache-2.0')
        expected = ({}, [Error(ERROR, "Invalid license key: apache-2.0")])
        assert expected == license_data


    @mock.patch.object(api, 'urlopen')
    def test_valid_api_url(self, mock_data):
        mock_data.return_value = ''
        assert api.valid_api_url('non_valid_url') is False

    @mock.patch('aboutcode.api.have_network_connection')
    @mock.patch('aboutcode.api.valid_api_url')
    def test_fetch_licenses(self, have_network_connection, valid_api_url):
        have_network_connection.return_value = True

        valid_api_url.return_value = False
        error_msg = (
            'Network problem. Please check your Internet connection. '
            'License retrieval is skipped.')
        expected = ({}, [Error(ERROR, error_msg)])
        assert api.fetch_licenses([], '', '') == expected

        valid_api_url.return_value = True
        expected = ({}, [])
        assert api.fetch_licenses([], '', '') == expected
