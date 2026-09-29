import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def load_demo():
    return json.loads(Path('examples/demo_scenario.json').read_text(encoding='utf-8'))


def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_plan_demo_returns_missions():
    r = client.post('/api/plan', json=load_demo())
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['summary']['coverage_strips'] > 0
    assert data['summary']['active_drones'] >= 1
    assert len(data['missions']) >= 1
    assert all(len(m['route']) >= 2 for m in data['missions'])


def test_optimization_modes_are_supported():
    for mode in ['min_time', 'min_airtime', 'balanced']:
        demo = load_demo()
        demo['optimization'] = mode
        r = client.post('/api/plan', json=demo)
        assert r.status_code == 200, r.text
        assert r.json()['summary']['optimization'] == mode


def test_exports():
    plan = client.post('/api/plan', json=load_demo()).json()
    gj = client.post('/api/export/geojson', json=plan)
    assert gj.status_code == 200
    assert gj.json()['type'] == 'FeatureCollection'
    kml = client.post('/api/export/kml', json=plan)
    assert kml.status_code == 200
    assert '<kml' in kml.text
