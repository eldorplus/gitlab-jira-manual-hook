from app.services.elastic_service import ElasticService


def test_index_is_daily():
    from datetime import datetime, timezone

    service = ElasticService("http://localhost:9200")
    assert service._index(datetime(2026, 8, 28, tzinfo=timezone.utc)) == "gitlab-pipelines-2026.08.28"
