from __future__ import unicode_literals

from fnmatch import filter as fnfilter

import pytest


def test_role():
    from ldap2pg.manager import Role

    role = Role(name='toto')

    assert 'toto' == role.name
    assert 'toto' == str(role)
    assert 'toto' in repr(role)

    roles = sorted([Role('b'), Role('a')])

    assert ['a', 'b'] == roles


def test_create():
    from ldap2pg.manager import Role

    role = Role(name='toto', members=['titi'])

    queries = [q.args[0] for q in role.create()]

    assert fnfilter(queries, "CREATE ROLE toto *;")
    assert fnfilter(queries, "GRANT toto TO titi;")


def test_alter():
    from ldap2pg.manager import Role

    a = Role(name='toto', members=['titi'], options=dict(LOGIN=True))
    b = Role(name='toto', members=['tata'], options=dict(LOGIN=False))

    queries = [q.args[0] for q in a.alter(a)]
    assert not queries

    queries = [q.args[0] for q in a.alter(b)]

    assert fnfilter(queries, "ALTER ROLE toto *;")
    assert fnfilter(queries, "GRANT toto TO tata;")
    assert fnfilter(queries, "REVOKE toto FROM titi;")


def test_drop():
    from ldap2pg.manager import Role

    role = Role(name='toto', members=['titi'])

    queries = [q.args[0] for q in role.drop()]

    assert fnfilter(queries, "*REASSIGN OWNED*DROP OWNED BY toto;*")
    assert fnfilter(queries, "DROP ROLE toto;")


def test_options():
    from ldap2pg.manager import RoleOptions

    options = RoleOptions()

    assert 'NOSUPERUSER' in repr(options)

    with pytest.raises(ValueError):
        options.update(dict(POUET=True))

    with pytest.raises(ValueError):
        RoleOptions(POUET=True)


def test_flatten():
    from ldap2pg.role import RoleSet, Role

    roles = RoleSet()
    roles.add(Role('parent0', members=['child0', 'child1']))
    roles.add(Role('parent1', members=['child2', 'child3']))
    roles.add(Role('parent2', members=['child4']))
    roles.add(Role('child0', members=['subchild0']))
    roles.add(Role('child1', members=['subchild1', 'subchild2']))
    roles.add(Role('child2', members=['outer0']))
    roles.add(Role('child3'))
    roles.add(Role('child4'))
    roles.add(Role('subchild0'))
    roles.add(Role('subchild1'))
    roles.add(Role('subchild2'))

    order = list(roles.flatten())

    wanted = [
        'subchild0',
        'child0',
        'subchild1',
        'subchild2',
        'child1',
        'child2',
        'child3',
        'child4',
        'parent0',
        'parent1',
        'parent2',
    ]

    assert wanted == order


def test_resolve_membership():
    from ldap2pg.role import RoleSet, Role

    alice = Role('alice')
    bob = Role('bob', members=['oscar'])
    oscar = Role('oscar', parents=['alice', 'bob'])

    roles = RoleSet([alice, bob, oscar])

    roles.resolve_membership()

    assert not oscar.parents
    assert 'oscar' in alice.members
