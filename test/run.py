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


def read_versions(name):
    lines = open(os.path.join(build_path(), name, 'VERSIONS')).readlines()
    return [line.strip() for line in lines if len(line) != 0]


def get_generic_versions(name, with_head):
    lines = read_versions(name)
    head = ['head'] if with_head else []
    return head + lines


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


def run(compiler, code, expected, stderr=False):
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
    ip = '127.0.0.1'
    r = requests.post('http://test-server:3500/api/compile.json', headers={'content-type': 'application/json', 'X-Real-IP': ip}, data=json.dumps(request))
    # print(r.json())
    assert 200 == r.status_code
    if r.json()['status'] != '0':
        print('{}: {}'.format(compiler, r.json()))
    assert r.json()['status'] == '0'
    if stderr:
        assert r.json()['program_error'] == expected
    else:
        assert r.json()['program_output'] == expected


def test_generic(name, test_file, expected, with_head, post_name='', head_versions=['head'], stderr=False):
    code = codecs.open(os.path.join('../build/{name}/resources'.format(name=name), test_file), 'r', 'utf-8').read()
    for cv in get_generic_versions(name, with_head=False):
        compiler = '{name}-{cv}'.format(name=name, cv=cv) + post_name
        add_test(compiler, lambda compiler=compiler: run(compiler, code, expected, stderr=stderr))

    if with_head:
        for cv in head_versions:
            compiler = '{name}-{cv}'.format(name=name, cv=cv) + post_name
            add_test(compiler, lambda compiler=compiler: run(compiler, codecs.open(os.path.join('../build/{name}-head/resources'.format(name=name), test_file), 'r', 'utf-8').read(), expected, stderr=stderr))


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


def test_gcc_c():
    code = codecs.open('../build/gcc/resources/test.c', 'r', 'utf-8').read()
    code_head = codecs.open('../build/gcc-head/resources/test.c', 'r', 'utf-8').read()
    code_gcc_1 = codecs.open('../build/gcc/resources/test_gcc_1.c', 'r', 'utf-8').read()

    for cv in get_generic_versions('gcc', with_head=True):
        compiler = 'gcc-{cv}-c'.format(cv=cv)
        if compiler.startswith('gcc-1.'):
            # gcc-1.xx
            add_test(compiler, lambda compiler=compiler: run(compiler, code_gcc_1, 'hello\n'))
        elif compiler.startswith('gcc-head'):
            # gcc-head
            add_test(compiler, lambda compiler=compiler: run(compiler, code_head, 'hello\n'))
        else:
            add_test(compiler, lambda compiler=compiler: run(compiler, code, 'hello\n'))


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


def test_icpc():
    code = codecs.open('../build/icc/resources/test.c', 'r', 'utf-8').read()
    for cv in get_generic_versions('icc', with_head=False):
        compiler = 'icpc-{cv}'.format(cv=cv)
        add_test(compiler, lambda compiler=compiler: run(compiler, code, 'hello\n'))


def test_preprocessor():
    compiler = 'gcc-head-pp'
    code = codecs.open('../build/gcc-head/resources/test.pp', 'r', 'utf-8').read()
    add_test(compiler, lambda: run(compiler, code, 'hello\n'))

    compiler = 'clang-head-pp'
    code = codecs.open('../build/clang-head/resources/test.pp', 'r', 'utf-8').read()
    add_test(compiler, lambda: run(compiler, code, 'hello\n'))


def test_rill_head():
    compiler = 'rill-head'
    code = codecs.open('../build/rill-head/resources/test.rill', 'r', 'utf-8').read()
    add_test(compiler, lambda: run(compiler, code, 'hello world\n'))


def test_gdc_head():
    compiler = 'gdc-head'
    code = codecs.open('../build/gdc-head/resources/test.d', 'r', 'utf-8').read()
    add_test(compiler, lambda: run(compiler, code, 'hello\n'))


def test_lazyk():
    compiler = 'lazyk'
    code = codecs.open('../build/lazyk/resources/test.lazy', 'r', 'utf-8').read()
    add_test(compiler, lambda: run(compiler, code, 'Hello, world\n'))


def test_bash():
    compiler = 'bash'
    code = codecs.open('../build/bash/resources/test.sh', 'r', 'utf-8').read()
    add_test(compiler, lambda: run(compiler, code, 'hello\n'))


def test_cmake_head():
    compiler = 'cmake-head'
    code = codecs.open('../build/cmake-head/resources/test.cmake', 'r', 'utf-8').read()
    add_test(compiler, lambda: run(compiler, code, '-- hello\n'))


def register():
    test_list()
    test_boost()
    test_boost_head()
    test_rill_head()
    test_gcc_c()
    test_generic(name='gcc', test_file='test.cpp', expected='hello\n', with_head=True)
    test_generic(name='clang', test_file='test.c', expected='hello\n', with_head=True, post_name='-c')
    test_generic(name='clang', test_file='test.cpp', expected='hello\n', with_head=True)
    test_generic(name='zapcc', test_file='test.cpp', expected='hello\n', with_head=False)
    test_generic(name='icc', test_file='test.c', expected='hello\n', with_head=False)
    test_icpc()
    test_preprocessor()
    test_generic(name='mono', test_file='test.cs', expected='hello\n', with_head=True)
    test_generic(name='erlang', test_file='prog.erl', expected='hello\n', with_head=True)
    test_generic(name='elixir', test_file='test.exs', expected='hello\n', with_head=True)
    test_generic(name='ghc', test_file='test.hs', expected='hello\n', with_head=True)
    test_gdc_head()
    test_generic(name='dmd', test_file='test.d', expected='hello\n', with_head=True)
    test_generic(name='ldc', test_file='test.d', expected='hello\n', with_head=True)
    test_generic(name='openjdk', test_file='prog.java', expected='hello\n', with_head=True)
    test_generic(name='rust', test_file='test.rs', expected='hello\n', with_head=True)
    test_generic(name='cpython', test_file='test.py', expected='hello\n', with_head=True, head_versions=['head', '2.7-head'])
    test_generic(name='ruby', test_file='test.rb', expected='hello\n', with_head=True)
    test_generic(name='mruby', test_file='test.rb', expected='hello\n', with_head=True)
    test_generic(name='scala', test_file='prog.scala', expected='hello\n', with_head=True, head_versions=read_versions('scala-head'))
    test_generic(name='groovy', test_file='test.groovy', expected='hello\n', with_head=True)
    test_generic(name='nodejs', test_file='test.js', expected='hello\n', with_head=True)
    test_generic(name='coffeescript', test_file='test.coffee', expected='hello\n', with_head=True)
    test_generic(name='spidermonkey', test_file='test.js', expected='hello\n', with_head=False)
    test_generic(name='swift', test_file='test.swift', expected='hello\n', with_head=True)
    test_generic(name='perl', test_file='test.pl', expected='hello\n', with_head=True)
    test_generic(name='php', test_file='test.php', expected='hello\n', with_head=True)
    test_generic(name='lua', test_file='test.lua', expected='hello\n', with_head=False)
    test_generic(name='luajit', test_file='test.lua', expected='hello\n', with_head=True)
    test_generic(name='sqlite', test_file='test.sql', expected='hello\n', with_head=True)
    test_generic(name='fpc', test_file='test.pas', expected='hello\n', with_head=True)
    test_generic(name='clisp', test_file='test.lisp', expected='hello\n', with_head=False)
    test_lazyk()
    test_generic(name='vim', test_file='test.vim', expected='hello', with_head=True, stderr=True)
    test_generic(name='pypy', test_file='test.py', expected='hello\n', with_head=True)
    test_generic(name='ocaml', test_file='test.ml', expected='Hello, world!\n', with_head=True)
    test_generic(name='go', test_file='test.go', expected='hello\n', with_head=True)
    test_generic(name='sbcl', test_file='test.lisp', expected='hello', with_head=True)
    test_generic(name='pony', test_file='test/main.pony', expected='hello\n', with_head=True)
    test_generic(name='crystal', test_file='test.cr', expected='hello\n', with_head=True)
    test_generic(name='nim', test_file='test.nim', expected='hello\n', with_head=True)
    test_generic(name='openssl', test_file='test.ssl.sh', expected='-----BEGIN RSA PRIVATE KEY-----\n', with_head=True)
    test_generic(name='emacs', test_file='test.el', expected='hello\n', with_head=False)
    test_generic(name='fsharp', test_file='test.fs', expected='hello\n', with_head=True)
    test_generic(name='dotnetcore', test_file='test.cs', expected='hello\n', with_head=True)
    test_generic(name='typescript', test_file='test.ts', expected='hello\n', with_head=False)
    test_cmake_head()
    test_generic(name='r', test_file='test.R', expected='hello', with_head=True)
    test_generic(name='julia', test_file='test.jl', expected='hello\n', with_head=True)
    test_bash()


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
