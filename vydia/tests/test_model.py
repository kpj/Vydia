import os

import pytest

import vydia


@pytest.fixture
def model(tmpdir):
    cfg = os.path.join(tmpdir, 'state.json')
    log = os.path.join(tmpdir, 'log.txt')

    m = vydia.core.Model(state_fname=cfg, log_fname=log)
    return m


def test_state_update(model):
    assert model._load_state() == {}

    model.update_state('pl01', {'id': '123'})
    assert model._load_state() == {'pl01': {'id': '123'}}

    model.update_state('pl02', {'id': 'ABC'})
    assert model._load_state() == {
        'pl01': {'id': '123'}, 'pl02': {'id': 'ABC'}}

    model.update_state('pl01', {'id': '___', 'foo': 42})
    assert model._load_state() == {
        'pl01': {'id': '___', 'foo': 42}, 'pl02': {'id': 'ABC'}}