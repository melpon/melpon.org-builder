# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import fnmatch
import codecs
import json
import requests
import pprint


def script_path():
    return os.path.dirname(os.path.realpath(__file__))


def build_path():
    return os.path.join(script_path(), '..', 'build')


# [(<boost-version>, <compiler>-head)]
def get_boost_head_versions():
    lines = codecs.open(os.path.join(build_path(), 'boost-head', 'VERSIONS'), 'r', 'utf-8').readlines()
    return [tuple(line.split()) for line in lines if len(line.strip()) != 0]


# [(<boost-version>, <compiler>, <compiler-version>)]
def get_boost_versions():
    lines = codecs.open(os.path.join(build_path(), 'boost', 'VERSIONS'), 'r', 'utf-8').readlines()
    return [tuple(line.split()) for line in lines if len(line.strip()) != 0]


# [(<boost-version>, <compiler>, <compiler-version>)]
def get_boost_versions_with_head():
    return get_boost_versions() + [(bv,) + tuple(c.split('-')) for bv, c in get_boost_head_versions()]


def get_gcc_versions():
    lines = codecs.open(os.path.join(build_path(), 'gcc', 'VERSIONS'), 'r', 'utf-8').readlines()
    return [line.strip() for line in lines if len(line) != 0]


def get_gcc_versions_with_head():
    return get_gcc_versions() + ['head']


def get_clang_versions():
    lines = codecs.open(os.path.join(build_path(), 'clang', 'VERSIONS'), 'r', 'utf-8').readlines()
    return [line.strip() for line in lines if len(line) != 0]


def get_clang_versions_with_head():
    return get_clang_versions() + ['head']


def get_mono_versions():
    lines = codecs.open(os.path.join(build_path(), 'mono', 'VERSIONS'), 'r', 'utf-8').readlines()
    return [line.strip() for line in lines if len(line) != 0]


def get_mono_versions_with_head():
    return get_mono_versions() + ['head']


__infos = None


def get_infos():
    global __infos
    if __infos is None:
        __infos = requests.get('http://test-server:3500/api/list.json').json()
    return __infos


def get_info(infos, name):
    for info in infos:
        if info['name'] == name:
            return info
    raise Exception('not found: {}'.format(name))


def test_list():
    def run():
        r = requests.get('http://test-server:3500/api/list.json')
        assert 200 == r.status_code
        v = json.loads(r.text)
        assert len(v) != 0
    add_test('list', run)


__tests = []


def add_test(name, func):
    global __tests
    __tests.append((name, func))


def run_tests(cond):
    global __tests
    for name, func in __tests:
        if not cond(name):
            continue
        try:
            func()
            print('{}: ok'.format(name))
        except Exception as e:
            print('{}: failed ({})'.format(name, e))


def get_tests():
    global __tests
    return [name for name, _ in __tests]


def run(compiler, code, expected):
    infos = get_infos()
    info = get_info(infos, compiler)
    opts = []
    for switch in info['switches']:
        if switch['type'] == 'single':
            if switch['default']:
                opts.append(switch['name'])
        elif switch['type'] == 'select':
            opts.append(switch['default'])
    request = {
        'compiler': compiler,
        'code': code,
        'options': ','.join(opts),
    }
    r = requests.post('http://test-server:3500/api/compile.json', headers={'content-type': 'application/json'}, data=json.dumps(request))
    assert 200 == r.status_code
    if r.json()['status'] != '0':
        print('{}: {}'.format(compiler, r.json()))
    assert r.json()['status'] == '0'
    assert r.json()['program_output'] == expected


def test_gcc():
    code = codecs.open('../build/gcc/resources/test.cpp', 'r', 'utf-8').read()
    for cv in get_gcc_versions():
        compiler = 'gcc-{cv}'.format(cv=cv)
        add_test(compiler, lambda: run(compiler, code, 'hello\n'))


def test_gcc_head():
    compiler = 'gcc-head'
    add_test(compiler, lambda: run(compiler, codecs.open('../build/gcc-head/resources/test.cpp', 'r', 'utf-8').read(), 'hello\n'))


def test_clang():
    code = codecs.open('../build/clang/resources/test.cpp', 'r', 'utf-8').read()
    for cv in get_clang_versions():
        compiler = 'clang-{cv}'.format(cv=cv)
        add_test(compiler, lambda: run(compiler, code, 'hello\n'))


def test_clang_head():
    compiler = 'clang-head'
    add_test(compiler, lambda: run(compiler, codecs.open('../build/clang-head/resources/test.cpp', 'r', 'utf-8').read(), 'hello\n'))


def test_mono():
    code = codecs.open('../build/mono/resources/test.cs', 'r', 'utf-8').read()
    for cv in get_mono_versions():
        compiler = 'mono-{cv}'.format(cv=cv)
        add_test(compiler, lambda: run(compiler, code, 'hello\n'))


def test_mono_head():
    compiler = 'mono-head'
    add_test(compiler, lambda: run(compiler, codecs.open('../build/mono-head/resources/test.cs', 'r', 'utf-8').read(), 'hello\n'))


def run_boost(version, compiler, compiler_version, code, expected):
    infos = get_infos()
    info = get_info(infos, '{}-{}'.format(compiler, compiler_version))
    opts = []
    for switch in info['switches']:
        if switch['type'] == 'single':
            if switch['default']:
                opts.append(switch['name'])
        elif switch['type'] == 'select':
            if 'boost' in switch['default']:
                opts.append('boost-{}-{}-{}'.format(version, compiler, compiler_version))
            else:
                opts.append(switch['default'])
    request = {
        'compiler': '{}-{}'.format(compiler, compiler_version),
        'code': code,
        'options': ','.join(opts),
    }

    r = requests.post('http://test-server:3500/api/compile.json', headers={'content-type': 'application/json'}, data=json.dumps(request))
    assert 200 == r.status_code
    if r.json()['status'] != '0':
        print('boost-{} for {}-{}: {}'.format(version, compiler, compiler_version, r.json()))
    assert r.json()['status'] == '0'
    assert r.json()['program_output'] == expected


def test_boost():
    code = codecs.open('../build/boost/resources/test.cpp', 'r', 'utf-8').read()
    for version, compiler, compiler_version in get_boost_versions():
        name = 'boost-{}-{}-{}'.format(version, compiler, compiler_version)
        add_test(name, lambda: run_boost(version, compiler, compiler_version, code, '23\n0\nSuccess\n'))


def test_boost_head():
    code = codecs.open('../build/boost-head/resources/test.cpp', 'r', 'utf-8').read()
    for version, compiler in get_boost_head_versions():
        name = 'boost-{}-{}'.format(version, compiler)
        compiler = compiler.split('-')[0]
        add_test(name, lambda: run_boost(version, compiler, 'head', code, '23\n0\nSuccess\n'))


def test_rill_head():
    compiler = 'rill-head'
    code = codecs.open('../build/rill-head/resources/test.rill', 'r', 'utf-8').read()
    add_test(compiler, lambda: run(compiler, code, 'hello world\n'))


def register():
    test_list()
    test_gcc()
    test_gcc_head()
    test_clang()
    test_clang_head()
    test_mono()
    test_mono_head()
    test_boost()
    test_boost_head()
    test_rill_head()


def main():
    if len(sys.argv) == 1:
        print('python run.py test1 [test2 [test3 [...]]]')
        print('python run.py --all')
        print()
        print('example:')
        print("  python run.py 'gcc-head'")
        print("  python run.py 'clang-*'")
        print("  python run.py 'boost-*-gcc-*' 'boost-1.6?.0-clang-*'")
        sys.exit(0)

    run_all = '--all' in sys.argv
    patterns = sys.argv[1:]

    register()
    def cond(name):
        if run_all:
            return True
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
    run_tests(cond)


if __name__ == '__main__':
    main()