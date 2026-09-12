import pytest
from django.contrib.auth import get_user_model

from apps.tipps.models import Tipp, TippVote

User = get_user_model()


@pytest.fixture
def user2(db):
    return User.objects.create_user(
        username="testuser2", password="test", email="test2@studentenportal.ch"
    )


@pytest.fixture
def tipps_with_votes(user, user2):
    """Create 3 tipps with different vote counts:
    tipp_popular: 2 upvotes (by user and user2)
    tipp_medium: 1 upvote (by user)
    tipp_new: 0 votes but newest
    """
    tipp_popular = Tipp.objects.create(
        author=user, summary="Popular Tipp", description="Very popular"
    )
    TippVote.objects.create(user=user, tipp=tipp_popular, vote=True)
    TippVote.objects.create(user=user2, tipp=tipp_popular, vote=True)

    tipp_medium = Tipp.objects.create(
        author=user, summary="Medium Tipp", description="Medium popular"
    )
    TippVote.objects.create(user=user, tipp=tipp_medium, vote=True)

    tipp_new = Tipp.objects.create(
        author=user, summary="New Tipp", description="Brand new"
    )

    return tipp_popular, tipp_medium, tipp_new


@pytest.mark.django_db
class TestTippListSorting:
    def test_default_sort_by_votes(self, auth_client, tipps_with_votes):
        tipp_popular, tipp_medium, tipp_new = tipps_with_votes
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        pos_popular = content.index("Popular Tipp")
        pos_medium = content.index("Medium Tipp")
        pos_new = content.index("New Tipp")
        assert pos_popular < pos_medium, "Popular tipp should appear before medium"
        assert pos_medium < pos_new, "Medium tipp should appear before new"

    def test_sort_by_votes_explicit(self, auth_client, tipps_with_votes):
        tipp_popular, tipp_medium, tipp_new = tipps_with_votes
        response = auth_client.get("/tipps/?sort=votes")
        content = response.content.decode()
        pos_popular = content.index("Popular Tipp")
        pos_new = content.index("New Tipp")
        assert pos_popular < pos_new

    def test_sort_by_date(self, auth_client, tipps_with_votes):
        tipp_popular, tipp_medium, tipp_new = tipps_with_votes
        response = auth_client.get("/tipps/?sort=date")
        content = response.content.decode()
        pos_new = content.index("New Tipp")
        pos_popular = content.index("Popular Tipp")
        assert pos_new < pos_popular, "Newest tipp should appear first when sorting by date"

    def test_sort_toggle_links_present(self, auth_client, tipps_with_votes):
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        assert "Beliebteste" in content
        assert "Neueste" in content


@pytest.mark.django_db
class TestTippListSearch:
    def test_search_by_summary(self, auth_client, user):
        Tipp.objects.create(author=user, summary="Python Tricks", description="desc")
        Tipp.objects.create(author=user, summary="Other Tipp", description="desc")
        response = auth_client.get("/tipps/?q=Python")
        content = response.content.decode()
        assert "Python Tricks" in content
        assert "Other Tipp" not in content

    def test_search_by_description(self, auth_client, user):
        Tipp.objects.create(author=user, summary="Tipp A", description="Use virtualenv")
        Tipp.objects.create(author=user, summary="Tipp B", description="Something else")
        response = auth_client.get("/tipps/?q=virtualenv")
        content = response.content.decode()
        assert "Tipp A" in content
        assert "Tipp B" not in content

    def test_search_no_results(self, auth_client, user):
        Tipp.objects.create(author=user, summary="Tipp A", description="desc")
        response = auth_client.get("/tipps/?q=nonexistent")
        content = response.content.decode()
        assert "Keine Tipps gefunden" in content

    def test_search_preserves_sort(self, auth_client, user):
        Tipp.objects.create(author=user, summary="Searchable", description="desc")
        response = auth_client.get("/tipps/?q=Searchable&sort=date")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Searchable" in content

    def test_search_term_persists_in_input(self, auth_client, user):
        Tipp.objects.create(author=user, summary="Tipp", description="desc")
        response = auth_client.get("/tipps/?q=findme")
        content = response.content.decode()
        assert 'value="findme"' in content


@pytest.mark.django_db
class TestTippMarkdownRendering:
    def test_markdown_rendered_in_list(self, auth_client, user):
        Tipp.objects.create(
            author=user, summary="MD Tipp", description="**bold text** and *italic*"
        )
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        assert "<strong>bold text</strong>" in content
        assert "<em>italic</em>" in content

    def test_xss_stripped_in_list(self, auth_client, user):
        Tipp.objects.create(
            author=user,
            summary="XSS Tipp",
            description="<script>alert('xss')</script>",
        )
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        assert "<script>" not in content
