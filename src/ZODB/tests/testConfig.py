##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import doctest
import tempfile
import unittest

import transaction
import ZODB.config
import ZODB.tests.util
from ZODB.POSException import ReadOnlyError


class ConfigTestBase(ZODB.tests.util.TestCase):
    def _opendb(self, s):
        return ZODB.config.databaseFromString(s)

    def tearDown(self):
        ZODB.tests.util.TestCase.tearDown(self)
        if getattr(self, "storage", None) is not None:
            self.storage.cleanup()

    def _test(self, s):
        db = self._opendb(s)
        self.storage = db._storage
        # Do something with the database to make sure it works
        cn = db.open()
        rt = cn.root()
        rt["test"] = 1
        transaction.commit()
        db.close()


class ZODBConfigTest(ConfigTestBase):
    def test_map_config1(self):
        self._test(
            """
            <zodb>
              <mappingstorage/>
            </zodb>
            """)

    def test_map_config2(self):
        self._test(
            """
            <zodb>
              <mappingstorage/>
              cache-size 1000
            </zodb>
            """)

    def test_file_config1(self):
        path = tempfile.mktemp()
        self._test(
            """
            <zodb>
              <filestorage>
                path %s
              </filestorage>
            </zodb>
            """ % path)

    def test_file_config2(self):
        path = tempfile.mktemp()
        cfg = """
        <zodb>
          <filestorage>
            path %s
            create false
            read-only true
          </filestorage>
        </zodb>
        """ % path
        self.assertRaises(ReadOnlyError, self._test, cfg)

    def test_demo_config(self):
        cfg = """
        <zodb unused-name>
          <demostorage>
            name foo
            <mappingstorage/>
          </demostorage>
        </zodb>
        """
        self._test(cfg)


def database_xrefs_config():
    r"""
    >>> db = ZODB.config.databaseFromString(
    ...    "<zodb>\n<mappingstorage>\n</mappingstorage>\n</zodb>\n")
    >>> db.xrefs
    True
    >>> db = ZODB.config.databaseFromString(
    ...    "<zodb>\nallow-implicit-cross-references true\n"
    ...    "<mappingstorage>\n</mappingstorage>\n</zodb>\n")
    >>> db.xrefs
    True
    >>> db = ZODB.config.databaseFromString(
    ...    "<zodb>\nallow-implicit-cross-references false\n"
    ...    "<mappingstorage>\n</mappingstorage>\n</zodb>\n")
    >>> db.xrefs
    False
    """

def multi_databases():
    r"""If there are multiple codb sections -> multidatabase

    >>> db = ZODB.config.databaseFromString('''
    ... <zodb>
    ...    <mappingstorage>
    ...    </mappingstorage>
    ... </zodb>
    ... <zodb Foo>
    ...    <mappingstorage>
    ...    </mappingstorage>
    ... </zodb>
    ... <zodb>
    ...    database-name Bar
    ...    <mappingstorage>
    ...    </mappingstorage>
    ... </zodb>
    ... ''')
    >>> sorted(db.databases)
    ['', 'Bar', 'foo']

    >>> db.database_name
    ''
    >>> db.databases[db.database_name] is db
    True
    >>> db.databases['foo'] is not db
    True
    >>> db.databases['Bar'] is not db
    True
    >>> db.databases['Bar'] is not db.databases['foo']
    True

    Can't have repeats:

    >>> ZODB.config.databaseFromString('''
    ... <zodb 1>
    ...    <mappingstorage>
    ...    </mappingstorage>
    ... </zodb>
    ... <zodb 1>
    ...    <mappingstorage>
    ...    </mappingstorage>
    ... </zodb>
    ... <zodb 1>
    ...    <mappingstorage>
    ...    </mappingstorage>
    ... </zodb>
    ... ''') # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    ConfigurationSyntaxError:
    section names must not be re-used within the same container:'1' (line 9)

    >>> ZODB.config.databaseFromString('''
    ... <zodb>
    ...    <mappingstorage>
    ...    </mappingstorage>
    ... </zodb>
    ... <zodb>
    ...    <mappingstorage>
    ...    </mappingstorage>
    ... </zodb>
    ... ''') # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    ValueError: database_name '' already in databases

    """

def test_blob_dir_permissions():
    """

    Blob directory permissions can be specified with the
    `blob-dir-permissions` option.

    >>> import os, tempfile
    >>> fd, path = tempfile.mkstemp()
    >>> os.close(fd)
    >>> blob_dir = tempfile.mkdtemp()
    >>> db = ZODB.config.databaseFromString('''
    ... <zodb>
    ...     <filestorage>
    ...        path %s
    ...        blob-dir %s
    ...        blob-dir-permissions 0770
    ...        create true
    ...     </filestorage>
    ... </zodb>
    ... ''' % (path, blob_dir))

    >>> oct(os.stat(db.storage.blob_dir).st_mode)
    '040770'

    The `blob-dir-permissions` option expects an octal.

    >>> ZODB.config.databaseFromString('''
    ... <zodb>
    ...     <filestorage>
    ...         path %s
    ...         blob-dir %s
    ...         blob-dir-permissions 888
    ...     </filestorage>
    ... </zodb>''' % (path, blob_dir,))
    Traceback (most recent call last):
    ...
    ValueError: Expected an octal for blob_dir_permissions option, got: '888'

    >>> ZODB.config.databaseFromString('''
    ... <zodb>
    ...     <filestorage>
    ...         path %s
    ...         blob-dir %s
    ...         blob-dir-permissions xxxx
    ...     </filestorage>
    ... </zodb>''' % (path, blob_dir,))
    Traceback (most recent call last):
    ...
    ValueError: Expected an octal for blob_dir_permissions option, got: 'xxxx'

    """

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(
        setUp=ZODB.tests.util.setUp, tearDown=ZODB.tests.util.tearDown))
    suite.addTest(unittest.makeSuite(ZODBConfigTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
