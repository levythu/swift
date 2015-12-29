# Copyright (c) 2012 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Unit tests for Name_check filter

Created on February 29, 2012

@author: eamonn-otoole
'''

import unittest

from swift.common.swob import Request, Response
from swift.common.middleware import name_check

MAX_LENGTH = 255
FORBIDDEN_CHARS = '\'\"<>`'
FORBIDDEN_REGEXP = "/\./|/\.\./|/\.$|/\.\.$"


class FakeApp(object):

    def __call__(self, env, start_response):
        return Response(body="OK")(env, start_response)


class TestNameCheckMiddleware(unittest.TestCase):

    def setUp(self):
        self.conf = {'maximum_length': MAX_LENGTH, 'forbidden_chars':
                     FORBIDDEN_CHARS, 'forbidden_regexp': FORBIDDEN_REGEXP}
        self.test_check = name_check.filter_factory(self.conf)(FakeApp())

    def test_valid_length_and_character(self):
        path = '/V1.0/' + 'c' * (MAX_LENGTH - 6)
        resp = Request.blank(path, environ={'REQUEST_METHOD': 'PUT'}
                             ).get_response(self.test_check)
        self.assertEqual(resp.body, 'OK')

    def test_invalid_character(self):
        for c in self.conf['forbidden_chars']:
            path = '/V1.0/1234' + c + '5'
            resp = Request.blank(
                path, environ={'REQUEST_METHOD': 'PUT'}).get_response(
                    self.test_check)
            self.assertEqual(
                resp.body,
                ("Object/Container/Account name contains forbidden chars "
                 "from %s" % self.conf['forbidden_chars']))
            self.assertEqual(resp.status_int, 400)

    def test_maximum_length_from_config(self):
        # test invalid length
        orig_test_check = self.test_check
        conf = {'maximum_length': "500"}
        self.test_check = name_check.filter_factory(conf)(FakeApp())
        path = '/V1.0/a/c' + 'o' * (500 - 8)
        resp = Request.blank(path, environ={'REQUEST_METHOD': 'PUT'}
                             ).get_response(self.test_check)
        self.assertEqual(
            resp.body,
            ("Object/Container/Account name longer than the allowed "
             "maximum 500"))
        self.assertEqual(resp.status_int, 400)

        # test valid length
        path = '/V1.0/a/c' + 'o' * (MAX_LENGTH - 10)
        resp = Request.blank(path, environ={'REQUEST_METHOD': 'PUT'}
                             ).get_response(self.test_check)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.body, 'OK')
        self.test_check = orig_test_check

    def test_invalid_length(self):
        path = '/V1.0/' + 'c' * (MAX_LENGTH - 5)
        resp = Request.blank(path, environ={'REQUEST_METHOD': 'PUT'}
                             ).get_response(self.test_check)
        self.assertEqual(
            resp.body,
            ("Object/Container/Account name longer than the allowed maximum %s"
             % self.conf['maximum_length']))
        self.assertEqual(resp.status_int, 400)

    def test_invalid_regexp(self):
        for s in ['/.', '/..', '/./foo', '/../foo']:
            path = '/V1.0/' + s
            resp = Request.blank(
                path, environ={'REQUEST_METHOD': 'PUT'}).get_response(
                    self.test_check)
            self.assertEqual(
                resp.body,
                ("Object/Container/Account name contains a forbidden "
                 "substring from regular expression %s"
                 % self.conf['forbidden_regexp']))
            self.assertEqual(resp.status_int, 400)

    def test_valid_regexp(self):
        for s in ['/...', '/.\.', '/foo']:
            path = '/V1.0/' + s
            resp = Request.blank(
                path, environ={'REQUEST_METHOD': 'PUT'}).get_response(
                    self.test_check)
            self.assertEqual(resp.body, 'OK')


if __name__ == '__main__':
    unittest.main()
