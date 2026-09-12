import pytest
from django.contrib.auth import get_user_model

from apps.tipps.models import Tipp, TippComment, TippVote

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


@pytest.mark.django_db
class TestTippEdit:
    def test_author_can_edit(self, auth_client, user):
        tipp = Tipp.objects.create(
            author=user, summary="Original", description="Original desc"
        )
        response = auth_client.get(f"/tipps/{tipp.pk}/edit/")
        assert response.status_code == 200
        assert "Original" in response.content.decode()

    def test_author_can_submit_edit(self, auth_client, user):
        tipp = Tipp.objects.create(
            author=user, summary="Original", description="Original desc"
        )
        response = auth_client.post(
            f"/tipps/{tipp.pk}/edit/",
            {"summary": "Updated", "description": "Updated desc"},
        )
        assert response.status_code == 302
        tipp.refresh_from_db()
        assert tipp.summary == "Updated"
        assert tipp.description == "Updated desc"

    def test_non_author_gets_403(self, auth_client, user, user2):
        tipp = Tipp.objects.create(
            author=user2, summary="Other", description="Other desc"
        )
        response = auth_client.get(f"/tipps/{tipp.pk}/edit/")
        assert response.status_code == 403

    def test_anonymous_redirected_to_login(self, client, user):
        tipp = Tipp.objects.create(
            author=user, summary="Test", description="desc"
        )
        response = client.get(f"/tipps/{tipp.pk}/edit/")
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_edit_button_visible_to_author(self, auth_client, user):
        Tipp.objects.create(author=user, summary="My Tipp", description="desc")
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        assert "Bearbeiten" in content

    def test_edit_button_not_visible_to_others(self, auth_client, user2):
        Tipp.objects.create(author=user2, summary="Other Tipp", description="desc")
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        assert "Bearbeiten" not in content


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="admin", password="test", email="admin@studentenportal.ch",
        is_staff=True,
    )


@pytest.fixture
def staff_client(client, staff_user):
    assert client.login(username="admin", password="test")
    return client


@pytest.mark.django_db
class TestTippCommentAdd:
    def test_authenticated_user_can_add_comment(self, auth_client, user):
        tipp = Tipp.objects.create(author=user, summary="Test", description="desc")
        response = auth_client.post(
            f"/tipps/{tipp.pk}/comment/add/",
            {"text": "Great tipp!"},
        )
        assert response.status_code == 302
        assert TippComment.objects.filter(tipp=tipp, text="Great tipp!").exists()

    def test_anonymous_cannot_add_comment(self, client, user):
        tipp = Tipp.objects.create(author=user, summary="Test", description="desc")
        response = client.post(
            f"/tipps/{tipp.pk}/comment/add/",
            {"text": "Nope"},
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url
        assert TippComment.objects.count() == 0

    def test_comment_sets_author(self, auth_client, user):
        tipp = Tipp.objects.create(author=user, summary="Test", description="desc")
        auth_client.post(f"/tipps/{tipp.pk}/comment/add/", {"text": "Comment"})
        comment = TippComment.objects.first()
        assert comment.author == user


@pytest.mark.django_db
class TestTippCommentEdit:
    def test_author_can_edit_comment(self, auth_client, user):
        tipp = Tipp.objects.create(author=user, summary="Test", description="desc")
        comment = TippComment.objects.create(tipp=tipp, author=user, text="Original")
        response = auth_client.post(
            f"/tipps/comment/{comment.pk}/edit/",
            {"text": "Updated"},
        )
        assert response.status_code == 302
        comment.refresh_from_db()
        assert comment.text == "Updated"

    def test_non_author_gets_403(self, auth_client, user, user2):
        tipp = Tipp.objects.create(author=user2, summary="Test", description="desc")
        comment = TippComment.objects.create(tipp=tipp, author=user2, text="Other")
        response = auth_client.get(f"/tipps/comment/{comment.pk}/edit/")
        assert response.status_code == 403

    def test_anonymous_redirected_to_login(self, client, user):
        tipp = Tipp.objects.create(author=user, summary="Test", description="desc")
        comment = TippComment.objects.create(tipp=tipp, author=user, text="Test")
        response = client.get(f"/tipps/comment/{comment.pk}/edit/")
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.django_db
class TestTippCommentDelete:
    def test_author_can_delete_comment(self, auth_client, user):
        tipp = Tipp.objects.create(author=user, summary="Test", description="desc")
        comment = TippComment.objects.create(tipp=tipp, author=user, text="Delete me")
        response = auth_client.post(f"/tipps/comment/{comment.pk}/delete/")
        assert response.status_code == 302
        assert TippComment.objects.count() == 0

    def test_admin_can_delete_any_comment(self, staff_client, user):
        tipp = Tipp.objects.create(author=user, summary="Test", description="desc")
        comment = TippComment.objects.create(tipp=tipp, author=user, text="Delete me")
        response = staff_client.post(f"/tipps/comment/{comment.pk}/delete/")
        assert response.status_code == 302
        assert TippComment.objects.count() == 0

    def test_non_author_non_admin_gets_403(self, auth_client, user, user2):
        tipp = Tipp.objects.create(author=user2, summary="Test", description="desc")
        comment = TippComment.objects.create(tipp=tipp, author=user2, text="Protected")
        response = auth_client.post(f"/tipps/comment/{comment.pk}/delete/")
        assert response.status_code == 403
        assert TippComment.objects.count() == 1


@pytest.mark.django_db
class TestTippCommentInList:
    def test_comment_count_displayed(self, auth_client, user):
        tipp = Tipp.objects.create(author=user, summary="Test", description="desc")
        TippComment.objects.create(tipp=tipp, author=user, text="Comment 1")
        TippComment.objects.create(tipp=tipp, author=user, text="Comment 2")
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        assert "2 Kommentare" in content

    def test_zero_comments_displayed(self, auth_client, user):
        Tipp.objects.create(author=user, summary="Test", description="desc")
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        assert "0 Kommentare" in content

    def test_comment_add_form_present_for_authenticated(self, auth_client, user):
        Tipp.objects.create(author=user, summary="Test", description="desc")
        response = auth_client.get("/tipps/")
        content = response.content.decode()
        assert "Kommentar hinzufügen" in content or 'name="text"' in content
