#!/usr/bin/env python
# -*- coding: utf8 -*-

# ============================================================================
#  Copyright (c) 2014-2018 nexB Inc. http://www.nexb.com/ - All rights reserved.
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

from collections import OrderedDict
import io
import json
import shutil
import unittest

from attributecode import CRITICAL
from attributecode import INFO
from attributecode import Error
from attributecode import inv
from attributecode import model
from attributecode.util import csv

from testing_utils import extract_test_loc
from testing_utils import get_temp_file
from testing_utils import get_test_loc
from attributecode.util import to_posix

try:
    # Python 2
    unicode  # NOQA
except NameError:  # pragma: nocover
    # Python 3
    unicode = str  # NOQA


def load_csv(location):
    """
    Read CSV at `location` and yield an ordered mapping for each row.
    """
    with io.open(location, encoding='utf-8') as csvfile:
        for row in csv.DictReader(csvfile):
            yield row

def check_csv(expected, result, regen=False):
    """
    Assert that the contents of two CSV files locations `expected` and
    `result` are equal.
    """
    if regen:
        shutil.copyfile(result, expected)
    expected = sorted([sorted(d.items()) for d in load_csv(expected)])
    result = [d.items() for d in load_csv(result)]
    result = sorted(sorted(items) for items in result)

    assert expected == result


def check_json(expected, result, regen=False):
    """
    Assert that the contents of two JSON files are equal.
    """

    with open(result) as r:
        result = json.load(r, object_pairs_hook=OrderedDict)

    if regen:
        with open(expected, 'wb') as o:
            o.write(json.dumps(result, indent=2))

    with open(expected) as e:
        expected = json.load(e, object_pairs_hook=OrderedDict)

    assert expected == result


def get_test_content(test_location):
    """
    Read file at test_location and return a unicode string.
    """
    return get_unicode_content(get_test_loc(test_location))


def get_unicode_content(location):
    """
    Read file at location and return a unicode string.
    """
    with io.open(location, encoding='utf-8') as doc:
        return doc.read()


def fix_location(abouts, test_dir):
    """
    Fix the about.location by removing the `test_dir` from the path.
    """
    for a in abouts:
        loc = a.location.replace(test_dir, '').strip('/\\')
        a.location = to_posix(loc)


class InventoryTest(unittest.TestCase):

    def test_collect_inventory_return_errors(self):
        test_loc = get_test_loc('test_inv/collect_inventory_errors')
        errors, _abouts = inv.collect_inventory(test_loc)
        expected_errors = [Error(INFO, 'Field date is a custom field.')]
        assert expected_errors == errors

    def test_collect_inventory_with_long_path(self):
        test_loc = extract_test_loc('test_inv/longpath.zip')
        _errors, abouts = inv.collect_inventory(test_loc)

        expected_paths = [
            'longpath/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/non-supported_date_format.ABOUT',
            'longpath/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/supported_date_format.ABOUT'
        ]
        fix_location(abouts, test_loc)

        assert sorted(expected_paths) == sorted([a.location for a in abouts])

        expected_name = ['distribute', 'date_test']
        result_name = [a.name for a in abouts]
        assert sorted(expected_name) == sorted(result_name)

    def test_collect_inventory_can_collect_a_single_file(self):
        test_loc = get_test_loc('test_inv/single_file/django_snippets_2413.ABOUT')
        errors, abouts = inv.collect_inventory(test_loc)
        expected = [
            Error(INFO, 'Field license_text_file is a custom field.'),
            Error(INFO, 'Field license_url is a custom field.'),
        ]

        assert expected == errors
        expected = [OrderedDict([
            ('about_resource', u'django_snippets_2413.py'),
            ('name', u'Yet another query string template tag'),
            ('version', u'2011-04-12'),
            ('download_url', u'http://djangosnippets.org/snippets/2413/download/'),
            ('homepage_url', u'http://djangosnippets.org/snippets/2413/'),
            ('notes', u'This file was modified to include the line "register = Library()" without which the template tag is not registered.'),
            (u'license_text_file', u'django_snippets.LICENSE'),
            (u'license_url', u'http://djangosnippets.org/about/tos/'),
        ])
        ]
        assert expected == [a.to_dict() for a in abouts]

    def test_collect_inventory_return_no_warnings_and_model_can_use_relative_paths(self):
        test_loc = get_test_loc('test_inv/rel/allAboutInOneDir')
        errors, _abouts = inv.collect_inventory(test_loc)
        expected_errors = []
        result = [(level, e) for level, e in errors if level > INFO]
        assert expected_errors == result

    def test_collect_inventory_populate_location(self):
        test_loc = get_test_loc('test_inv/complete')
        errors, abouts = inv.collect_inventory(test_loc)
        expected = [
            Error(INFO, 'Field author is a custom field.'),
            Error(INFO, 'Field license_file is a custom field.'),
            Error(INFO, 'Field license_key is a custom field.'),
        ]

        assert expected == errors

        fix_location(abouts, test_loc)

        expected = [OrderedDict([
            ('about_resource', u'.'),
            ('name', u'AboutCode'),
            ('version', u'0.11.0'),
            ('description', u'AboutCode is a tool \nto process ABOUT files. \nAn ABOUT file is a file.'),
            ('homepage_url', u'http://dejacode.org'),
            ('license_expression', u'apache-2.0'),
            ('licenses', [OrderedDict([('key', u'apache-2.0'), ('file', u'apache-2.0.LICENSE')])]),
            ('copyright', u'Copyright (c) 2013-2014 nexB Inc.'),
            ('notice_file', u'NOTICE'),
            ('owner', u'nexB Inc.'),
            ('vcs_tool', u'git'),
            ('vcs_repository', u'https://github.com/dejacode/about-code-tool.git'),
            (u'author', [u'Jillian Daguil', u'Chin Yeung Li', u'Philippe Ombredanne', u'Thomas Druez']),
            (u'license_file', u'apache-2.0.LICENSE'),
            (u'license_key', u'apache-2.0'),
        ])]
        assert expected == [a.to_dict() for a in abouts]

    def test_collect_inventory_with_multi_line(self):
        test_loc = get_test_loc('test_inv/multi_line_license_expression.ABOUT')
        errors, abouts = inv.collect_inventory(test_loc)
        assert [] == errors
        expected = [
            'https://enterprise.dejacode.com/urn/?urn=urn:dje:license:mit',
            'https://enterprise.dejacode.com/urn/?urn=urn:dje:license:apache-2.0']
        results = [l.url for l in abouts[0].licenses]
        assert expected == results

        assert 'mit or apache-2.0' == abouts[0].license_expression

    def test_collect_inventory_always_collects_custom_fields(self):
        test_loc = get_test_loc('test_inv/custom_fields.ABOUT')
        errors, abouts = inv.collect_inventory(test_loc)
        expected = [
            Error(INFO, 'Field custom_mapping is a custom field.'),
            Error(INFO, 'Field resource is a custom field.'),
        ]

        assert expected == errors
        assert {'custom_mapping': 'test', 'resource': '.'} == abouts[0].custom_fields

    def test_collect_inventory_does_not_raise_error_and_maintains_order_on_custom_fields(self):
        test_loc = get_test_loc('test_inv/custom_fields2.ABOUT')
        errors, abouts = inv.collect_inventory(test_loc)
        expected_errors = [
            Error(INFO, 'Field custom_mapping is a custom field.'),
            Error(INFO, 'Field resource is a custom field.'),
        ]
        assert expected_errors == errors

        expected = [OrderedDict([
            ('about_resource', u'.'),
            ('name', u'test'),
            (u'custom_mapping', u'test'),
            (u'resource', u'.')])]
        assert expected == [a.to_dict() for a in abouts]

    def test_collect_inventory_works_with_relative_paths(self):
        # FIXME: This test need to be run under src/attributecode/
        # or otherwise it will fail as the test depends on the launching
        # location
        test_loc = get_test_loc('test_inv/relative')
        # Use '.' as the indication of the current directory
        test_loc1 = test_loc + '/./'
        # Use '..' to go back to the parent directory
        test_loc2 = test_loc + '/../relative'
        errors1, abouts1 = inv.collect_inventory(test_loc1)
        expected_errors = [
            Error(INFO, 'Field author is a custom field.'),
            Error(INFO, 'Field license_file is a custom field.'),
            Error(INFO, 'Field license_key is a custom field.'),
        ]
        assert expected_errors == errors1
        expected = [OrderedDict([
            ('about_resource', u'.'),
            ('name', u'AboutCode'),
            ('version', u'0.11.0'),
            ('description', u'AboutCode is a tool \nto process ABOUT files. \nAn ABOUT file is a file.'),
            ('homepage_url', u'http://dejacode.org'),
            ('license_expression', u'apache-2.0'),
            ('licenses', [OrderedDict([('key', u'apache-2.0'), ('file', u'apache-2.0.LICENSE')])]),
            ('copyright', u'Copyright (c) 2013-2014 nexB Inc.'),
            ('notice_file', u'NOTICE'),
            ('owner', u'nexB Inc.'),
            ('vcs_tool', u'git'),
            ('vcs_repository', u'https://github.com/dejacode/about-code-tool.git'),
            (u'author', [u'Jillian Daguil', u'Chin Yeung Li', u'Philippe Ombredanne', u'Thomas Druez']),
            (u'license_file', u'apache-2.0.LICENSE'),
            (u'license_key', u'apache-2.0'),
        ])]
        assert expected == [a.to_dict() for a in abouts1]

        errors2, abouts2 = inv.collect_inventory(test_loc2)
        assert expected_errors == errors2
        assert expected == [a.to_dict() for a in abouts2]

    def test_collect_inventory_basic_from_directory(self):
        test_dir = get_test_loc('test_inv/basic')
        result_file = get_temp_file()
        errors, abouts = inv.collect_inventory(test_dir)

        fix_location(abouts, test_dir)

        inv.save_as_csv(result_file, abouts)

        expected_errors = [
            Error(INFO, 'Field author is a custom field.'),
            Error(INFO, 'Field license_file is a custom field.'),
            Error(INFO, 'Field license_key is a custom field.'),
        ]

        assert expected_errors == sorted(errors)

        expected = get_test_loc('test_inv/basic/expected.csv')
        check_csv(expected, result_file)

    def test_collect_inventory_with_about_resource_path_from_directory(self):
        test_dir = get_test_loc('test_inv/basic_with_about_resource_path')
        result_file = get_temp_file()
        errors, abouts = inv.collect_inventory(test_dir)

        fix_location(abouts, test_dir)

        inv.save_as_csv(result_file, abouts)

        expected_errors = []
        assert expected_errors == errors
        expected = get_test_loc('test_inv/basic_with_about_resource_path/expected.csv')
        check_csv(expected, result_file)

    def test_collect_inventory_with_no_about_resource_from_directory(self):
        test_dir = get_test_loc('test_inv/no_about_resource_key')
        result_file = get_temp_file()
        errors, abouts = inv.collect_inventory(test_dir)
        fix_location(abouts, test_dir)

        inv.save_as_csv(result_file, abouts)

        expected_errors = [
            Error(CRITICAL,
                  'Field about_resource is required and empty or missing.')]
        assert expected_errors == errors

        expected = get_test_loc('test_inv/no_about_resource_key/expected.csv')
        check_csv(expected, result_file)

    def test_collect_inventory_complex_from_directory(self):
        test_dir = get_test_loc('test_inv/complex')
        result_file = get_temp_file()
        errors, abouts = inv.collect_inventory(test_dir)
        fix_location(abouts, test_dir)

        inv.save_as_csv(result_file, abouts)

        assert all(e.severity == INFO for e in errors)

        expected = get_test_loc('test_inv/complex/expected.csv')
        check_csv(expected, result_file)

    def test_collect_inventory_does_not_damage_line_endings(self):
        test_dir = get_test_loc('test_inv/crlf/about.ABOUT')
        result_file = get_temp_file()
        errors, abouts = inv.collect_inventory(test_dir)
        fix_location(abouts, get_test_loc('test_inv/crlf'))

        errors2 = inv.save_as_csv(result_file, abouts)
        errors.extend(errors2)

        assert all(e.severity == INFO for e in errors)

        expected = get_test_loc('test_inv/crlf/expected.csv')
        check_csv(expected, result_file)

    def test_write_output_csv(self):
        test_file = get_test_loc('test_inv/this.ABOUT')
        about = model.About.load(test_file)

        fix_location([about], get_test_loc('test_inv'))

        result_file = get_temp_file()
        inv.save_as_csv(result_file, [about])

        expected = get_test_loc('test_inv/expected.csv')
        check_csv(expected, result_file)

    def test_write_output_json(self):
        test_file = get_test_loc('test_inv/this.ABOUT')
        about = model.About.load(location=test_file)

        fix_location([about], get_test_loc('test_inv'))

        result_file = get_temp_file()
        inv.save_as_json(result_file, [about])

        expected = get_test_loc('test_inv/expected.json')
        check_json(expected, result_file)

    def test_is_about_file(self):
        assert inv.is_about_file('test.About')
        assert inv.is_about_file('test2.aboUT')
        assert not inv.is_about_file('no_about_ext.something')
        assert not inv.is_about_file('about')
        assert not inv.is_about_file('about.txt')

    def test_is_about_file_is_false_if_only_bare_extension(self):
        assert not inv.is_about_file('.ABOUT')


class TestGetLocations(unittest.TestCase):

    def test_get_locations(self):
        test_dir = get_test_loc('test_inv/about_locations')
        expected = sorted([
            'file with_spaces.ABOUT',
            'file1',
            'file2',
            'dir1/file2',
            'dir1/file2.aBout',
            'dir1/dir2/file1.about',
            'dir2/file1'])

        result = sorted(inv.get_locations(test_dir))
        result = [l.partition('/about_locations/')[-1] for l in result]
        assert expected == result

    def test_get_about_locations(self):
        test_dir = get_test_loc('test_inv/about_locations')
        expected = sorted([
            'file with_spaces.ABOUT',
            'dir1/file2.aBout',
            'dir1/dir2/file1.about',
        ])

        result = sorted(inv.get_about_locations(test_dir))
        result = [l.partition('/about_locations/')[-1] for l in result]
        assert expected == result

    def test_get_locations_can_yield_a_single_file(self):
        test_file = get_test_loc('test_inv/about_locations/file with_spaces.ABOUT')
        result = list(inv.get_locations(test_file))
        assert 1 == len(result)

    def test_get_about_locations_for_about(self):
        location = get_test_loc('test_inv/get_about_locations')
        result = list(inv.get_about_locations(location))
        expected = 'get_about_locations/about.ABOUT'
        assert result[0].endswith(expected)

    # FIXME: these are not very long/deep paths
    def test_get_locations_with_very_long_path(self):
        longpath = (
            'longpath'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
            '/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1/longpath1'
        )
        test_loc = extract_test_loc('test_inv/locations/longpath.zip')
        result = list(inv.get_locations(test_loc))
        assert any(longpath in r for r in result)