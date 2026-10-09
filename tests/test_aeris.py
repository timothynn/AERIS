from fastapi.testclient import TestClient
from app.domain import simulate, shift_time, distance_km, CODES
from app.main import create_app

def test_baseline_scenario():
    result=simulate('AE-204',0,0,100)
    assert result['delay_minutes']==0
    assert result['risk']=='NOMINAL'
    assert result['projected_arrival']=='08:50'

def test_severity_and_capacity():
    r=simulate('AE-204',100,100,10)
    assert r['delay_minutes']>90
    assert r['risk']=='ELEVATED'

def test_distance():
    assert 400<distance_km(CODES['HKJK'],CODES['HKMO'])<500
    assert shift_time('23:50',20)=='00:10'

def test_api_saves_history(tmp_path):
    with TestClient(create_app(str(tmp_path/'aeris.sqlite'))) as client:
        flights=client.get('/api/flights').json()['flights']
        assert len(flights)==8
        response=client.post('/api/simulate',json={'flight_id':'AE-204','weather_severity':40,'congestion':40,'runway_capacity':70,'save':True})
        assert response.status_code==200
        assert response.json()['saved_scenario_id']>=1
        assert len(client.get('/api/scenarios').json()['scenarios'])==1
        assert client.get('/api/weather?icao=HKJK').json()['source']=='SCENARIO_FIXTURE'
        assert client.post('/api/simulate',json={'weather_severity':200}).status_code==422
        assert client.post('/api/simulate',json={'flight_id':'NOT_REAL'}).status_code==404
