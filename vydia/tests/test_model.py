import os

import pytest

from ..core.model import Model


@pytest.fixture
def model(tmpdir: str) -> Model:
    cfg = os.path.join(tmpdir, 'state.json')
    log = os.path.join(tmpdir, 'log.txt')

    m = Model(state_fname=cfg, log_fname=log)
    return m


def test_state_update(model: Model) -> None:
    assert model._load_state() == {}

    model.update_state('pl01', {'id': '123'})
    assert model._load_state() == {'pl01': {'id': '123'}}

    model.update_state('pl02', {'id': 'ABC'})
    assert model._load_state() == {
        'pl01': {'id': '123'}, 'pl02': {'id': 'ABC'}}

    model.update_state('pl01', {'id': '___', 'foo': 42})
    assert model._load_state() == {
        'pl01': {'id': '___', 'foo': 42}, 'pl02': {'id': 'ABC'}}

    model.update_state('pl01', {'id': 'qux', 'foo': {'bar': 42, 'baz': 13}})
    assert model._load_state() == {
        'pl01': {'id': 'qux', 'foo': {'bar': 42, 'baz': 13}}, 'pl02': {'id': 'ABC'}}
